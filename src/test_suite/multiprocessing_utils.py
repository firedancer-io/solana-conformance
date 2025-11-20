from dataclasses import dataclass, field
from test_suite.constants import OUTPUT_BUFFER_SIZE
from test_suite.fuzz_context import ENTRYPOINT_HARNESS_MAP, HarnessCtx
from test_suite.fuzz_interface import ContextType, EffectsType
import test_suite.protos.invoke_pb2 as invoke_pb
import test_suite.protos.type_pb2 as type_pb
import test_suite.protos.metadata_pb2 as metadata_pb2
import ctypes
from ctypes import c_uint64, c_int, POINTER
import shutil
import subprocess
from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format, message
import os
import sys
import time
import zipfile
import threading
import io
from datetime import datetime
from test_suite.fuzzcorp_auth import get_fuzzcorp_auth
from test_suite.fuzzcorp_api_client import FuzzCorpAPIClient

# Thread-safe deduplication variables
_download_cache_lock = threading.Lock()
_extracted_fixtures = set()
_downloaded_artifact_hashes = set()


def extract_fix_files_from_zip(
    zip_data: bytes, target_dir: Path, enable_deduplication: bool = True
) -> int:
    fix_count = 0

    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        for member in z.namelist():
            if member.endswith(".fix"):
                fix_content = z.read(member)
                fix_name = Path(member).name
                fix_path = target_dir / fix_name

                if enable_deduplication:
                    with _download_cache_lock:
                        # Skip if fixture already exists on disk (never overwrite)
                        if fix_path.exists():
                            existing_size = fix_path.stat().st_size
                            new_size = len(fix_content)
                            print(
                                f"  WARNING: Skipping {fix_name} (exists on disk: {existing_size} bytes, new: {new_size} bytes)",
                                file=sys.stderr,
                                flush=True,
                            )
                            continue

                        # Skip if we've already extracted this fixture in this session
                        if fix_name in _extracted_fixtures:
                            continue
                        _extracted_fixtures.add(fix_name)

                with open(fix_path, "wb") as f:
                    f.write(fix_content)
                fix_count += 1

    return fix_count


def _download_with_timing(download_func, log_prefix: str):
    """
    Helper to execute a download function, time it, and log the speed.

    Args:
        download_func: Callable that returns the downloaded bytes
        log_prefix: Prefix for the log message (e.g., "  [lineage/hash]")

    Returns:
        bytes: The downloaded data
    """
    start_time = time.time()
    data = download_func()
    elapsed_time = time.time() - start_time

    # Calculate and log download speed
    size_bytes = len(data)
    size_mib = size_bytes / (1024 * 1024)
    speed_mibs = size_mib / elapsed_time if elapsed_time > 0 else 0

    print(
        f"{log_prefix}: {size_mib:.2f} MiB @ {speed_mibs:.2f} MiB/s",
        file=sys.stderr,
        flush=True,
    )

    return data


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
    try:
        fixture = invoke_pb.InstrFixture()
        if fixture_file.suffix == ".txt":
            with open(fixture_file, "r") as f:
                text_format.Parse(f.read(), fixture)
        else:
            with open(fixture_file, "rb") as f:
                fixture.ParseFromString(f.read())
        return fixture.metadata
    except Exception as e:
        print(f"Failed to parse fixture metadata: {e}")
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


def initialize_process_globals_for_extraction(output_dir):
    """
    Initialize globals needed for fixture context extraction in worker processes.

    Args:
        - output_dir (Path): Output directory for extracted contexts.
    """
    globals.output_dir = output_dir


def initialize_process_globals_for_decoding(output_dir, default_harness_ctx):
    """
    Initialize globals needed for protobuf decoding in worker processes.

    Args:
        - output_dir (Path): Output directory for decoded messages.
        - default_harness_ctx: Default harness context for decoding.
    """
    globals.output_dir = output_dir
    globals.default_harness_ctx = default_harness_ctx


def initialize_process_globals_for_download(
    output_dir, inputs_dir, repro_metadata_cache=None
):
    """
    Initialize globals needed for downloading fixtures/crashes in worker processes.

    Args:
        - output_dir (Path): Base output directory.
        - inputs_dir (Path): Directory for downloaded fixtures.
        - repro_metadata_cache (dict, optional): Cache of repro metadata.
    """
    globals.output_dir = output_dir
    globals.inputs_dir = inputs_dir
    if repro_metadata_cache is not None:
        globals.repro_metadata_cache = repro_metadata_cache


def initialize_process_globals_for_regeneration(
    output_dir,
    reference_shared_library,
    shared_library_path,
    log_level,
    features_to_add,
    features_to_remove,
    rekey_features,
    regenerate_dry_run,
    regenerate_verbose,
):
    """
    Initialize globals needed for fixture regeneration in worker processes.

    Args:
        - output_dir (Path): Output directory for regenerated fixtures.
        - reference_shared_library (Path): Path to reference shared library.
        - shared_library_path (Path): Path to shared library to load.
        - log_level (int): Logging level for the shared library.
        - features_to_add (set): Set of feature IDs to add.
        - features_to_remove (set): Set of feature IDs to remove.
        - rekey_features (list): List of (old, new) feature ID tuples.
        - regenerate_dry_run (bool): Whether to run in dry-run mode.
        - regenerate_verbose (bool): Whether to print verbose output.
    """
    import test_suite.features_utils as features_utils

    globals.output_dir = output_dir
    globals.reference_shared_library = reference_shared_library
    globals.features_to_add = features_to_add
    globals.features_to_remove = features_to_remove
    globals.rekey_features = rekey_features
    globals.regenerate_dry_run = regenerate_dry_run
    globals.regenerate_verbose = regenerate_verbose

    # Load the shared library in this worker process
    lib = ctypes.CDLL(shared_library_path)
    lib.sol_compat_init(log_level)
    globals.target_libraries = {shared_library_path: lib}

    # Get target features from the library in this worker process
    # (must be done per-process as it involves ctypes calls)
    globals.target_features = features_utils.get_sol_compat_features_t(lib)

    # Initialize output buffers for regeneration
    initialize_process_output_buffers()


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
    try:
        section_name, crash_hash = source

        out_dir = globals.inputs_dir / f"{section_name}_{crash_hash}"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Use FuzzCorp HTTP API to download repro
        config = get_fuzzcorp_auth(interactive=False)
        if not config:
            return {
                "success": False,
                "repro": f"{section_name}/{crash_hash}",
                "message": "Failed to download: no FuzzCorp config",
            }

        # Check if metadata is cached (to avoid slow API calls)
        repro_metadata = None
        if (
            hasattr(globals, "repro_metadata_cache")
            and globals.repro_metadata_cache is not None
            and crash_hash in globals.repro_metadata_cache
        ):
            repro_metadata = globals.repro_metadata_cache[crash_hash]
        else:
            # Meta data cache miss, fetch from API
            print(
                f"  Fetching metadata for {crash_hash[:16]}...",
                file=sys.stderr,
                flush=True,
            )
            with FuzzCorpAPIClient(
                api_origin=config.get_api_origin(),
                token=config.get_token(),
                org=config.get_organization(),
                project=config.get_project(),
                http2=True,
            ) as client:
                # Get repro metadata to find artifact hashes
                repro_metadata = client.get_repro_by_hash(
                    crash_hash,
                    org=config.get_organization(),
                    project=config.get_project(),
                )

        if not repro_metadata.artifact_hashes:
            return {
                "success": False,
                "repro": f"{section_name}/{crash_hash}",
                "message": "Failed to process: no artifacts found",
            }

        # Determine which artifacts to download
        download_all = getattr(globals, "download_all_artifacts", False)
        if download_all:
            artifacts_to_download = repro_metadata.artifact_hashes
            print(
                f"  [{section_name}/{crash_hash[:8]}] Downloading all {len(artifacts_to_download)} artifact(s)",
                file=sys.stderr,
                flush=True,
            )
        else:
            # Take only the first artifact hash
            artifacts_to_download = [repro_metadata.artifact_hashes[0]]
            print(
                f"  [{section_name}/{crash_hash[:8]}] Using first artifact: {artifacts_to_download[0][:16]}",
                file=sys.stderr,
                flush=True,
            )

        # Download and extract artifacts
        fix_count = 0
        was_cached = False

        # Create artifact cache directory in output folder
        artifact_cache_dir = globals.output_dir / ".artifact_cache"
        artifact_cache_dir.mkdir(parents=True, exist_ok=True)

        for idx, artifact_hash in enumerate(artifacts_to_download, 1):
            # Check if artifact ZIP already exists on disk
            artifact_zip_path = artifact_cache_dir / f"{artifact_hash}.zip"

            if artifact_zip_path.exists():
                # Use cached ZIP file
                was_cached = True
                with open(artifact_zip_path, "rb") as f:
                    artifact_data = f.read()
            else:
                # Download artifact (ZIP file)

                # Create HTTP client for artifact download
                with FuzzCorpAPIClient(
                    api_origin=config.get_api_origin(),
                    token=config.get_token(),
                    org=config.get_organization(),
                    project=config.get_project(),
                    http2=True,
                ) as client:
                    artifact_desc = (
                        f"Downloading artifact {idx}/{len(artifacts_to_download)}"
                        if len(artifacts_to_download) > 1
                        else "Downloading artifact"
                    )
                    artifact_label = (
                        f"[{idx}/{len(artifacts_to_download)}]"
                        if len(artifacts_to_download) > 1
                        else ""
                    )

                    artifact_data = _download_with_timing(
                        lambda: client.download_artifact_data(
                            artifact_hash,
                            section_name,
                            desc=artifact_desc,
                        ),
                        f"  [{section_name}/{crash_hash[:8]}] Artifact {artifact_label}",
                    )

                    # Save to cache for future runs
                    with open(artifact_zip_path, "wb") as f:
                        f.write(artifact_data)

            # Extract .fix files from the artifact ZIP
            fix_count += extract_fix_files_from_zip(
                artifact_data, globals.inputs_dir, enable_deduplication=True
            )

            # Mark this artifact as processed (in-memory only, for this session)
            with _download_cache_lock:
                _downloaded_artifact_hashes.add(artifact_hash)

        # Always return success if we processed artifacts (even if no new fixtures extracted)
        # Not extracting new fixtures just means they already exist or artifacts don't contain .fix files
        artifact_msg = (
            f"{len(artifacts_to_download)} artifact(s)"
            if len(artifacts_to_download) > 1
            else "latest artifact"
        )
        return {
            "success": True,
            "repro": f"{section_name}/{crash_hash}",
            "fixtures": fix_count,
            "cached": was_cached,
            "message": f"Processed {section_name}/{crash_hash} successfully ({fix_count} new fixture(s) from {artifact_msg})",
        }
    except Exception as e:
        return {
            "success": False,
            "repro": f"{section_name}/{crash_hash}",
            "message": f"Error: {type(e).__name__}: {str(e)}",
        }


def download_single_crash(source):
    try:
        lineage, crash_hash = source

        # Ensure output directory is set by caller
        if not hasattr(globals, "output_dir") or globals.output_dir is None:
            return {
                "success": False,
                "repro": f"{lineage}/{crash_hash}",
                "message": "No output_dir configured",
            }

        # Prefer lineage from metadata cache if available
        if hasattr(globals, "repro_metadata_cache") and crash_hash in getattr(
            globals, "repro_metadata_cache", {}
        ):
            meta = globals.repro_metadata_cache[crash_hash]
            if getattr(meta, "lineage", None):
                lineage = meta.lineage

        crashes_dir = globals.output_dir / "crashes" / lineage
        crashes_dir.mkdir(parents=True, exist_ok=True)
        out_path = crashes_dir / f"{crash_hash}.crash"

        # Skip if already exists
        if out_path.exists():
            return {
                "success": True,
                "repro": f"{lineage}/{crash_hash}",
                "cached": 1,
                "downloaded": 0,
                "path": str(out_path),
            }

        config = get_fuzzcorp_auth(interactive=False)
        if not config:
            return {
                "success": False,
                "repro": f"{lineage}/{crash_hash}",
                "message": "Failed to download: no FuzzCorp config",
            }

        with FuzzCorpAPIClient(
            api_origin=config.get_api_origin(),
            token=config.get_token(),
            org=config.get_organization(),
            project=config.get_project(),
            http2=True,
        ) as client:
            data = _download_with_timing(
                lambda: client.download_repro_data(
                    crash_hash,
                    lineage,
                    desc=f"Downloading {crash_hash[:8]}.crash",
                ),
                f"  [{lineage}/{crash_hash[:8]}] Crash file",
            )

            with open(out_path, "wb") as f:
                f.write(data)

        return {
            "success": True,
            "repro": f"{lineage}/{crash_hash}",
            "cached": 0,
            "downloaded": 1,
            "path": str(out_path),
        }
    except Exception as e:
        return {
            "success": False,
            "repro": f"{lineage}/{crash_hash}",
            "message": f"Error: {type(e).__name__}: {str(e)}",
        }
