import fd58
import inspect
from test_suite import features_utils, pb_utils
from test_suite.constants import NATIVE_PROGRAM_MAPPING
from test_suite.fuzz_context import (
    ENTRYPOINT_HARNESS_MAP,
    HarnessCtx,
    HARNESS_MAP,
    FIXTURE_EXTENSION,
    get_harness_for_entrypoint,
)
from test_suite.multiprocessing_utils import (
    build_test_results,
    extract_metadata,
    read_context,
    read_fixture,
    process_single_test_case,
)
import test_suite.globals as globals
import test_suite.protos.context_pb2 as context_pb
import test_suite.protos.invoke_pb2 as invoke_pb
import test_suite.protos.metadata_pb2 as metadata_pb
from google.protobuf import text_format
from pathlib import Path
from test_suite.fuzz_interface import ContextType, FixtureType
from test_suite.flatbuffers_utils import (
    convert_pb_to_fb_elf_fixture,
    detect_format,
    is_flatbuffers_output_supported,
    FLATBUFFERS_AVAILABLE,
)


def create_fixture(test_file: Path) -> int:
    """
    Create instruction fixture for an instruction context and effects.

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts

    Returns:
        - int: 1 on success, 0 on failure
    """

    harness_ctx = globals.default_harness_ctx
    source_format = "protobuf"  # Default for context files

    if test_file.suffix == FIXTURE_EXTENSION:
        # Detect the source format for .fix files
        try:
            with open(test_file, "rb") as f:
                raw_data = f.read()
            source_format = detect_format(raw_data)
            if source_format == "unknown":
                source_format = "protobuf"  # Default fallback
        except Exception:
            source_format = "protobuf"

        fixture = read_fixture(test_file)
        harness_ctx = get_harness_for_entrypoint(fixture.metadata.fn_entrypoint)
        fixture = create_fixture_from_context(harness_ctx, fixture.input)
    else:
        fixture = create_fixture_from_context(
            harness_ctx,
            read_context(globals.default_harness_ctx, test_file),
        )

    if fixture is None:
        return 0

    return write_fixture_to_disk(
        harness_ctx,
        test_file.stem,
        fixture.SerializeToString(deterministic=True),
        source_format=source_format,
    )


def create_fixture_from_context(
    harness_ctx: HarnessCtx, context: ContextType
) -> FixtureType | None:
    if context is None:
        return None

    context.DiscardUnknownFields()

    # Execute the test case
    results = process_single_test_case(harness_ctx, context)
    if results is None:
        return None

    pruned_results = harness_ctx.prune_effects_fn(context, results)

    # This is only relevant when you gather results for multiple targets
    if globals.only_keep_passing:
        status, _ = build_test_results(
            harness_ctx, pruned_results, globals.reference_shared_library
        )
        if status != 1:
            return None

    if pruned_results is None:
        return None

    effects_serialized = pruned_results[globals.reference_shared_library]

    if effects_serialized is None:
        return None

    # Create instruction fixture
    effects = harness_ctx.effects_type()
    effects.ParseFromString(effects_serialized)

    metadata = metadata_pb.FixtureMetadata()
    metadata.fn_entrypoint = harness_ctx.fuzz_fn_name
    fixture = harness_ctx.fixture_type()
    fixture.input.MergeFrom(context)
    fixture.output.MergeFrom(effects)
    fixture.metadata.MergeFrom(metadata)

    return fixture


def write_fixture_to_disk(
    harness_ctx: HarnessCtx,
    file_stem: str,
    serialized_fixture: str,
    source_format: str = "protobuf",
) -> int:
    """
    Writes instruction fixtures to disk. This function outputs in binary format unless
    specified otherwise with the --readable flag.

    Output format is controlled by globals.output_format:
    - 'auto': Upgrade to FlatBuffers when supported, otherwise Protobuf
    - 'protobuf': Binary Protobuf format (.fix) or human-readable (.fix.txt with -r)
    - 'flatbuffers': FlatBuffers binary format (.fix)

    Args:
        - harness_ctx (HarnessCtx): Harness context
        - file_stem (str): File stem
        - serialized_fixture (str): Serialized Protobuf fixture
        - source_format (str): Format of the source file ('protobuf' or 'flatbuffers')

    Returns:
        - int: 0 on failure, 1 on success
    """
    if serialized_fixture is None:
        return 0

    output_dir = globals.output_dir

    if globals.organize_fixture_dir:
        fixture = harness_ctx.fixture_type()
        fixture.ParseFromString(serialized_fixture)
        program_type = get_program_type(fixture)
        output_dir = output_dir / program_type
        output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output format
    output_format = getattr(globals, "output_format", "auto")

    # Check if FlatBuffers output is supported for this harness type
    # Currently only ELFLoaderFixture has FlatBuffers schema
    fb_supported = is_flatbuffers_output_supported(harness_ctx.fuzz_fn_name)

    # Handle 'auto' mode: upgrade to FlatBuffers when supported
    # This helps migrate the corpus to the newer format
    if output_format == "auto":
        if fb_supported:
            if source_format == "protobuf":
                print(f"Upgrading {file_stem} from Protobuf to FlatBuffers format")
            output_format = "flatbuffers"
        else:
            output_format = "protobuf"

    if output_format == "flatbuffers":
        # Check if FlatBuffers is available
        if not FLATBUFFERS_AVAILABLE:
            print(
                f"Warning: FlatBuffers output requested but not available. Falling back to Protobuf."
            )
            output_format = "protobuf"
        # Check if this fixture type supports FlatBuffers
        elif not fb_supported:
            # Only warn once per harness type (not for every file)
            output_format = "protobuf"
        else:
            # Deserialize Protobuf fixture
            fixture = harness_ctx.fixture_type()
            fixture.ParseFromString(serialized_fixture)

            # Convert to FlatBuffers
            fb_data, error = convert_pb_to_fb_elf_fixture(fixture)
            if error:
                print(
                    f"Warning: FlatBuffers conversion failed for {file_stem}: {error}. Falling back to Protobuf."
                )
                output_format = "protobuf"
            else:
                with open(output_dir / (file_stem + FIXTURE_EXTENSION), "wb") as f:
                    f.write(fb_data)
                return 1

    # Protobuf output (default)
    if globals.readable:
        # Deserialize fixture
        fixture = invoke_pb.InstrFixture()
        fixture.ParseFromString(serialized_fixture)

        # Encode fields for instruction context and effects
        context = harness_ctx.context_type()
        context.CopyFrom(fixture.input)
        # encode_input(context)
        harness_ctx.context_human_encode_fn(context)

        instr_effects = harness_ctx.effects_type()
        instr_effects.CopyFrom(fixture.output)
        harness_ctx.effects_human_encode_fn(instr_effects)

        fixture.input.CopyFrom(context)
        fixture.output.CopyFrom(instr_effects)

        with open(output_dir / (file_stem + ".fix.txt"), "w") as f:
            f.write(text_format.MessageToString(fixture, print_unknown_fields=False))
    else:
        with open(output_dir / (file_stem + FIXTURE_EXTENSION), "wb") as f:
            f.write(serialized_fixture)

    return 1


def extract_context_from_fixture(fixture_file: Path):
    """
    Extract InstrContext from InstrEffects and write to disk.

    Args:
        - fixture_file (Path): Path to fixture file

    Returns:
        - int: 1 on success, 0 on failure
    """
    try:
        fn_entrypoint = extract_metadata(fixture_file).fn_entrypoint
        harness_ctx = get_harness_for_entrypoint(fn_entrypoint)
        fixture = harness_ctx.fixture_type()
        with open(fixture_file, "rb") as f:
            fixture.ParseFromString(f.read())

        with open(globals.output_dir / (fixture_file.stem + ".bin"), "wb") as f:
            f.write(fixture.input.SerializeToString(deterministic=True))
    except:
        return 0

    return 1


def get_program_type(instr_fixture: invoke_pb.InstrFixture) -> str:
    """
    Get the program type based on the program / loader id.

    Args:
        - fixture (invoke_pb.InstrFixture): Instruction fixture

    Returns:
        - str | None: Program type (unknown if not found)
    """
    # Check if the program type can be deduced from program_id
    program_id = fd58.enc32(instr_fixture.input.program_id).decode()

    program_type = NATIVE_PROGRAM_MAPPING.get(program_id, None)
    if program_type:
        return program_type

    # Use the program_id owner instead (loader_id may not be reliable)
    for account_state in instr_fixture.input.accounts:
        if account_state.address == instr_fixture.input.program_id:
            program_type = NATIVE_PROGRAM_MAPPING.get(
                fd58.enc32(account_state.owner).decode(), "unknown"
            )
            if program_type != "unknown":
                program_type += "-programs"
            return program_type

    return "unknown"


def regenerate_fixture(test_file: Path) -> int:
    if test_file.is_dir():
        return 0

    # Detect the source format to preserve it in output
    source_format = "protobuf"
    try:
        with open(test_file, "rb") as f:
            raw_data = f.read()
        source_format = detect_format(raw_data)
        if source_format == "unknown":
            source_format = "protobuf"
    except Exception:
        source_format = "protobuf"

    fixture = read_fixture(test_file)
    harness_ctx = get_harness_for_entrypoint(fixture.metadata.fn_entrypoint)

    features_path = pb_utils.find_field_with_type(
        harness_ctx.context_type.DESCRIPTOR, context_pb.FeatureSet.DESCRIPTOR
    )

    # TODO: support multiple FeatureSet fields
    assert len(features_path) == 1, "Only one FeatureSet field is supported"
    features_path = features_path[0]

    features = pb_utils.access_nested_field_safe(fixture.input, features_path)
    original_feature_set = set(features.features) if features else set()
    new_feature_set = (
        original_feature_set | globals.features_to_add
    ) - globals.features_to_remove

    for old_feature, new_feature in globals.rekey_features:
        if old_feature in new_feature_set:
            new_feature_set.remove(old_feature)
            new_feature_set.add(new_feature)

    if globals.regenerate_dry_run:
        if globals.regenerate_verbose:
            print(f"Would regenerate {test_file}")
    else:
        if globals.regenerate_verbose:
            print(f"Regenerating {test_file}")

        # Apply minimum compatible features
        if features is not None:
            features.features[:] = sorted(list(new_feature_set))

        # Apply any custom transformations to the data
        harness_ctx.regenerate_transformation_fn(fixture)

        regenerated_fixture = create_fixture_from_context(harness_ctx, fixture.input)

        if regenerated_fixture is None:
            return 0

        write_fixture_to_disk(
            harness_ctx,
            test_file.stem,
            regenerated_fixture.SerializeToString(),
            source_format=source_format,
        )
    return 1
