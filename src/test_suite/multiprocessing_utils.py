from dataclasses import dataclass, field
from test_suite.constants import OUTPUT_BUFFER_SIZE
from test_suite.fuzz_context import ENTRYPOINT_HARNESS_MAP, HarnessCtx
from test_suite.fuzz_interface import ContextType, EffectsType
import test_suite.invoke_pb2 as invoke_pb
import test_suite.type_pb2 as type_pb
import test_suite.metadata_pb2 as metadata_pb2
import ctypes
from ctypes import c_uint64, c_int, POINTER
import shutil
import subprocess
from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format, message
from google.protobuf.internal.decoder import _DecodeVarint
import os
import re


def process_target(
    harness_ctx: HarnessCtx, library: ctypes.CDLL, context: ContextType
) -> invoke_pb.InstrEffects | None:
    """
    Process an instruction through a provided shared library and return the result.

    Args:
        - library (ctypes.CDLL): Shared library to process instructions.
        - serialized_instruction_context (str): Serialized instruction context message.

    Returns:
        - invoke_pb.InstrEffects | None: Result of instruction execution.
    """

    serialized_instruction_context = context.SerializeToString(deterministic=True)
    if serialized_instruction_context is None:
        return None

    # Prepare input data and output buffers
    in_data = serialized_instruction_context
    in_ptr = (ctypes.c_uint8 * len(in_data))(*in_data)
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(OUTPUT_BUFFER_SIZE)

    # Get the function to call
    sol_compat_fn = getattr(library, harness_ctx.fuzz_fn_name)

    # Define argument and return types
    sol_compat_fn.argtypes = [
        POINTER(ctypes.c_uint8),  # out_ptr
        POINTER(c_uint64),  # out_psz
        POINTER(ctypes.c_uint8),  # in_ptr
        c_uint64,  # in_sz
    ]
    sol_compat_fn.restype = c_int

    # Call the function
    result = sol_compat_fn(
        globals.output_buffer_pointer, ctypes.byref(out_sz), in_ptr, in_sz
    )
    # Result == 0 means execution failed
    if result == 0:
        return None

    # Process the output
    output_data = bytearray(globals.output_buffer_pointer[: out_sz.value])
    output_object = harness_ctx.effects_type()
    output_object.ParseFromString(output_data)

    return output_object


def extract_metadata(fixture_file: Path) -> str | None:
    """
    Extracts metadata from a fixture file.

    Args:
        - fixture_file (Path): Path to the fixture message.

    Returns:
        - str | None: Metadata from the fixture file.
    """

    if fixture_file.suffix == ".txt":
        with open(fixture_file, "r") as f:
            fixture_txt = f.read()
            metadata_txt = re.search(r"metadata\s*\{(.*?)\}", fixture_txt, re.DOTALL)
            if not metadata_txt:
                raise ValueError("No 'metadata { ... }' block found!")
            metadata_body = metadata_txt.group(1).strip()
            fixture_metadata = metadata_pb2.FixtureMetadata()
            text_format.Parse(metadata_body, fixture_metadata)
            return fixture_metadata

    with open(fixture_file, "rb") as f:
        proto_bytes = f.read()
        try:
            metadata = metadata_pb2.FixtureMetadata()
            pos = 0
            while pos < len(proto_bytes):
                tag, pos = _DecodeVarint(proto_bytes, pos)
                if (tag >> 3) == 1:
                    length, pos = _DecodeVarint(proto_bytes, pos)
                    metadata.ParseFromString(proto_bytes[pos : pos + length])
                    return metadata
                pos += _DecodeVarint(proto_bytes, pos)[0]
            raise message.DecodeError("No 'metadata' found")
        except message.DecodeError as e:
            print(f"Failed to parse 'metadata': {e}")
            return None


def read_context(harness_ctx: HarnessCtx, test_file: Path) -> message.Message | None:
    """
    Reads in test files and generates an Context Protobuf object for a test case.

    Args:
        - test_file (Path): Path to the context message.

    Returns:
        - message.Message | None: Instruction context, or None if reading failed.
    """
    # Try to read in first as binary-encoded Protobuf messages
    try:
        # Read in binary Protobuf messages
        with open(test_file, "rb") as f:
            context = harness_ctx.context_type()
            context.ParseFromString(f.read())
    except:
        try:
            # Maybe it's in human-readable Protobuf format?
            with open(test_file) as f:
                context = text_format.Parse(f.read(), harness_ctx.context_type())

            # Decode into digestable fields
            # decode_input(instruction_context)
            harness_ctx.context_human_decode_fn(context)
        except:
            # Unable to read message, skip and continue
            context = None

    if context is None:
        # Unreadable file, skip it
        return None

    # Discard unknown fields
    context.DiscardUnknownFields()
    return context


def read_fixture(fixture_file: Path) -> message.Message | None:
    """
    Reads in test files and generates an Fixture Protobuf object for a test case.

    DOES NOT SUPPORT HUMAN READABLE MESSAGES!!!

    Args:
        - fixture_file (Path): Path to the fixture message.

    Returns:
        - message.Message | None: Fixture, or None if reading failed.

    """
    # Try to read in first as binary-encoded Protobuf messages
    try:
        # Read in binary Protobuf messages
        fn_entrypoint = extract_metadata(fixture_file).fn_entrypoint
        harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
        with open(fixture_file, "rb") as f:
            fixture = harness_ctx.fixture_type()
            fixture.ParseFromString(f.read())
    except:
        try:
            # Maybe it's in human-readable Protobuf format?
            fn_entrypoint = extract_metadata(fixture_file).fn_entrypoint
            harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
            with open(fixture_file) as f:
                fixture = text_format.Parse(f.read(), harness_ctx.fixture_type())
            harness_ctx.context_human_decode_fn(fixture.input)
        except:
            # Unable to read message, skip and continue
            fixture = None

    if fixture is None:
        # Unreadable file, skip it
        return None

    # Discard unknown fields
    fixture.DiscardUnknownFields()
    return fixture


def decode_single_test_case(test_file: Path) -> int:
    """
    Decode a single test case into a human-readable message

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - int: 1 if successfully decoded and written, 0 if skipped.
    """
    if test_file.suffix == ".fix":
        fn_entrypoint = extract_metadata(test_file).fn_entrypoint
        harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
        fixture = read_fixture(test_file)
        serialized_protobuf = fixture.SerializeToString(deterministic=True)
    else:
        harness_ctx = globals.default_harness_ctx
        context = read_context(harness_ctx, test_file)
        serialized_protobuf = context.SerializeToString(deterministic=True)

    # Skip if input is invalid
    if serialized_protobuf is None:
        return 0

    # Encode the input fields to be human readable
    if test_file.suffix == ".fix":
        output = harness_ctx.fixture_type()
    else:
        output = harness_ctx.context_type()

    output.ParseFromString(serialized_protobuf)

    if test_file.suffix == ".fix":
        harness_ctx.context_human_encode_fn(output.input)
        harness_ctx.effects_human_encode_fn(output.output)
    else:
        harness_ctx.context_human_encode_fn(output)

    with open(globals.output_dir / (test_file.stem + ".txt"), "w") as f:
        f.write(text_format.MessageToString(output, print_unknown_fields=False))
    return 1


def process_single_test_case(
    harness_ctx: HarnessCtx,
    context: ContextType | None,
) -> dict[str, str | None] | None:
    """
    Process a single execution context (file, serialized instruction context) through
    all target libraries and returns serialized instruction effects.

    Args:
        - serialized_instruction_context (str | None): Serialized instruction context.

    Returns:
        - dict[str, str | None] | None: Dictionary of target library names and instruction effects.
    """
    # Mark as skipped if instruction context doesn't exist

    # Execute test case on each target library
    results = {}
    for target in globals.target_libraries:
        instruction_effects = process_target(
            harness_ctx,
            globals.target_libraries[target],
            context,
        )
        result = (
            instruction_effects.SerializeToString(deterministic=True)
            if instruction_effects
            else None
        )
        results[target] = result
    return results


def merge_results_over_iterations(results: tuple) -> tuple[str, dict]:
    """
    Merge results over separate iterations for a single test case.

    Args:
        - results (tuple): Tuple of (file stem, result for each target) for each iteration for a single test case.

    Returns:
        - tuple[str, dict]: Tuple of file stem and merged results over all iterations for single test case.
    """
    file = None
    merged_results = {}
    for target in globals.target_libraries:
        merged_results[target] = {}

        for iteration in range(globals.n_iterations):
            file_stem, execution_result = results[iteration]
            file = file_stem

            if execution_result is None:
                merged_results[target][iteration] = None
                continue

            merged_results[target][iteration] = execution_result[target]

    return file, merged_results


def build_test_results(
    harness_ctx: HarnessCtx, results: dict[str, str | None], reference_target: Path
) -> tuple[int, dict | None]:
    """
    Build a single result of single test execution and returns whether the test passed or failed.

    Args:
        - harness_ctx (HarnessCtx): Harness context.
        - results (dict[str, str | None]): Dictionary of target library names and serialized instruction effects.
        - reference_target (Path): Path to the reference target.

    Returns:
        - tuple[int, dict | None]: Tuple of:
            - 1 if passed, -1 if failed, 0 if skipped
            - Dictionary of target library names and file-dumpable serialized instruction effects
    """
    # If no results or Agave rejects input, mark case as skipped
    if results is None:
        # Mark as skipped (0)
        return 0, None

    outputs = {target: "None\n" for target in results}

    ref_result = results[reference_target]

    if ref_result is None:
        print("Skipping test case due to Agave rejection")
        return 0, None

    ref_effects = harness_ctx.effects_type()
    ref_effects.ParseFromString(ref_result)

    # Log execution results
    all_passed = True
    for target, result in results.items():
        if target == reference_target:
            continue
        # Create a Protobuf struct to compare and output, if applicable
        effects = None
        if result is not None:
            # Turn bytes into human readable fields
            effects = harness_ctx.effects_type()
            effects.ParseFromString(result)

            if globals.consensus_mode:
                harness_ctx.diff_effect_fn = harness_ctx.consensus_diff_effect_fn
            if globals.core_bpf_mode:
                harness_ctx.diff_effect_fn = harness_ctx.core_bpf_diff_effect_fn
            if globals.ignore_compute_units_mode:
                harness_ctx.diff_effect_fn = (
                    harness_ctx.ignore_compute_units_diff_effect_fn
                )

            # Note: diff_effect_fn may modify effects in-place
            all_passed &= harness_ctx.diff_effect_fn(ref_effects, effects)

            harness_ctx.effects_human_encode_fn(effects)
            outputs[target] = text_format.MessageToString(effects)
        else:
            all_passed = False

    harness_ctx.effects_human_encode_fn(ref_effects)
    outputs[reference_target] = text_format.MessageToString(ref_effects)

    # 1 = passed, -1 = failed
    return 1 if all_passed else -1, outputs


def initialize_process_output_buffers(randomize_output_buffer=False):
    """
    Initialize shared memory and pointers for output buffers for each process.

    Args:
        - randomize_output_buffer (bool): Whether to randomize output buffer.
    """
    globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)()

    if randomize_output_buffer:
        output_buffer_random_bytes = os.urandom(OUTPUT_BUFFER_SIZE)
        globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)(
            *output_buffer_random_bytes
        )


def run_test(test_file: Path) -> tuple[str, int, dict | None]:
    """
    Runs a single test from start to finish.

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - tuple[str, int, dict | None]: Tuple of:
            - File stem
            - 1 if passed, -1 if failed, 0 if skipped
            - Dictionary of target library names and file-dumpable serialized instruction effects
    """
    # Process fixtures through this entrypoint as well
    if test_file.suffix == ".fix":
        fn_entrypoint = extract_metadata(test_file).fn_entrypoint
        harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
        context = read_fixture(test_file).input
    else:
        harness_ctx = globals.default_harness_ctx
        context = read_context(harness_ctx, test_file)
        if context is None:
            fn_entrypoint = extract_metadata(test_file).fn_entrypoint
            harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
            context = read_fixture(test_file).input

    results = process_single_test_case(harness_ctx, context)
    pruned_results = harness_ctx.prune_effects_fn(context, results)
    return test_file.stem, *build_test_results(
        harness_ctx, pruned_results, globals.reference_shared_library
    )


def execute_fixture(test_file: Path) -> tuple[str, int, dict | None]:
    if test_file.suffix != ".fix":
        print(f"File {test_file} is not a fixture")
        return test_file.stem, None

    fn_entrypoint = extract_metadata(test_file).fn_entrypoint
    harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
    fixture = read_fixture(test_file)
    context = fixture.input
    output = fixture.output

    effects = process_target(
        harness_ctx, globals.target_libraries[globals.reference_shared_library], context
    )

    results = {
        Path("expected"): output.SerializeToString(deterministic=True),
        Path("actual"): (
            effects.SerializeToString(deterministic=True) if effects else None
        ),
    }
    prune_results = harness_ctx.prune_effects_fn(context, results)

    return test_file.stem, *build_test_results(
        harness_ctx, prune_results, Path("expected")
    )


def download_and_process(source):
    if isinstance(source, (tuple, list)) and len(source) == 2:
        section_name, crash_hash = source
        out_dir = globals.inputs_dir / f"{section_name}_{crash_hash}"
        out_dir.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "fuzz",
                "download",
                "repro",
                "--lineage",
                section_name,
                "--out-dir",
                str(out_dir),
                crash_hash,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        for fix in out_dir.rglob("*.fix"):
            shutil.copy2(fix, globals.inputs_dir)
        return f"Processed {section_name}/{crash_hash} successfully"

    else:
        zip_name = source.split("/")[-1]

        # Step 1: Download the file
        result = subprocess.run(
            ["wget", "-q", source, "-O", f"{globals.output_dir}/{zip_name}"],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            ["unzip", f"{globals.output_dir}/{zip_name}", "-d", globals.output_dir],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            f"mv {globals.output_dir}/repro_custom/*.fix {globals.inputs_dir}",
            shell=True,
            capture_output=True,
            text=True,
        )
        return f"Processed {zip_name} successfully"

    return f"Unsupported source: {source}"
