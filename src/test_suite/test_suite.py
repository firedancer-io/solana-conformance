import shutil
from typing import List
import typer
import ctypes
from multiprocessing import Pool
from pathlib import Path
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
from test_suite.fixture_utils import (
    create_fixture,
    extract_context_from_fixture,
)
from test_suite.multiprocessing_utils import (
    decode_single_test_case,
    read_context,
    initialize_process_output_buffers,
    process_target,
    run_test,
)
import test_suite.globals as globals
from test_suite.debugger import debug_host
from test_suite.util import set_ld_preload_asan
import resource
import tqdm
from test_suite.fuzz_context import *
import os

"""
Harness options:
- InstrHarness
- TxnHarness
- SyscallHarness
- ValidateVM
- ElfHarness
"""
harness_type = os.getenv("HARNESS_TYPE")
if harness_type:
    globals.harness_ctx = eval(harness_type)
else:
    globals.harness_ctx = InstrHarness

app = typer.Typer(
    help="Validate instruction effects from clients using instruction context Protobuf messages."
)


@app.command()
def exec_instr(
    file_or_dir: Path = typer.Option(
        None,
        "--input",
        "-i",
        help=f"Input {globals.harness_ctx.context_type.__name__} file or directory of files",
    ),
    shared_library: Path = typer.Option(
        Path("impl/firedancer/build/native/clang/lib/libfd_exec_sol_compat.so"),
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
):
    print(globals.harness_ctx)
    # Initialize output buffers and shared library
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)
    try:
        lib = ctypes.CDLL(shared_library)
    except:
        set_ld_preload_asan()
    lib.sol_compat_init()

    files_to_exec = file_or_dir.iterdir() if file_or_dir.is_dir() else [file_or_dir]
    for file in files_to_exec:
        print(f"Handling {file}...")
        context = read_context(file)
        assert context is not None, f"Unable to read {file.name}"

        # Execute and cleanup
        effects = process_target(lib, context)

        if not effects:
            print("No instruction effects returned")
            continue

        serialized_effects = effects.SerializeToString(deterministic=True)

        # Prune execution results
        serialized_effects = globals.harness_ctx.prune_effects_fn(
            context,
            {shared_library: serialized_effects},
        )[shared_library]

        parsed_instruction_effects = globals.harness_ctx.effects_type()
        parsed_instruction_effects.ParseFromString(serialized_effects)

        # Print human-readable output
        if parsed_instruction_effects:
            globals.harness_ctx.effects_human_encode_fn(parsed_instruction_effects)

        print(parsed_instruction_effects)

    lib.sol_compat_fini()


@app.command()
def debug_instr(
    file: Path = typer.Option(None, "--input", "-i", help="Input file"),
    shared_library: Path = typer.Option(
        Path("impl/lib/libsolfuzz_firedancer.so"),
        "--target",
        "-t",
        help="Shared object (.so) target file path to debug",
    ),
    debugger: str = typer.Option(
        "gdb", "--debugger", "-d", help="Debugger to use (gdb, rust-gdb)"
    ),
):
    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"Processing {file.name}...")

    # Decode the file and pass it into GDB
    instruction_context = read_context(file)
    assert instruction_context is not None, f"Unable to read {file.name}"
    debug_host(shared_library, instruction_context, gdb=debugger)


@app.command()
def instr_from_fixtures(
    input_dir: Path = typer.Option(
        Path("fixtures"),
        "--input-dir",
        "-i",
        help=f"Input directory containing {globals.harness_ctx.fixture_type.__name__} messages",
    ),
    output_dir: Path = typer.Option(
        Path("instr"),
        "--output-dir",
        "-o",
        help=f"Output directory for {globals.harness_ctx.context_type.__name__} messages",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
):
    # Specify globals
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    test_cases = list(input_dir.iterdir())
    num_test_cases = len(test_cases)

    print(f"Converting to {globals.harness_ctx.context_type.__name__}...")
    results = []
    with Pool(processes=num_processes) as pool:
        for result in tqdm.tqdm(
            pool.imap(extract_context_from_fixture, test_cases),
            total=num_test_cases,
        ):
            results.append(result)

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(results)} total files seen")
    print(f"{sum(results)} files successfully written")


@app.command()
def create_fixtures(
    input_dir: Path = typer.Option(
        Path("corpus8"),
        "--input-dir",
        "-i",
        help=f"Input directory containing {globals.harness_ctx.context_type.__name__} messages",
    ),
    solana_shared_library: Path = typer.Option(
        Path("impl/lib/libsolfuzz_agave_v2.0.so"),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [],
        "--target",
        "-t",
        help="Shared object (.so) target file paths (pairs with --keep-passing)."
        f" Targets must have {globals.harness_ctx.fuzz_fn_name} defined",
    ),
    output_dir: Path = typer.Option(
        Path("test_fixtures"),
        "--output-dir",
        "-o",
        help="Output directory for fixtures",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    readable: bool = typer.Option(
        False, "--readable", "-r", help="Output fixtures in human-readable format"
    ),
    only_keep_passing: bool = typer.Option(
        False, "--keep-passing", "-k", help="Only keep passing test cases"
    ),
    organize_fixture_dir: bool = typer.Option(
        False, "--group-by-program", "-g", help="Group fixture output by program type"
    ),
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library
    globals.readable = readable
    globals.only_keep_passing = only_keep_passing
    globals.organize_fixture_dir = organize_fixture_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize shared library
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        globals.target_libraries[target] = lib

    test_cases = list(input_dir.iterdir())
    num_test_cases = len(test_cases)

    # Generate the test cases in parallel from files on disk
    print("Creating fixtures...")
    write_results = []
    with Pool(
        processes=num_processes, initializer=initialize_process_output_buffers
    ) as pool:
        for result in tqdm.tqdm(
            pool.imap(
                create_fixture,
                test_cases,
            ),
            total=num_test_cases,
        ):
            write_results.append(result)

    # Clean up
    print("Cleaning up...")
    for target in shared_libraries:
        globals.target_libraries[target].sol_compat_fini()

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")


@app.command()
def run_tests(
    input_dir: Path = typer.Option(
        Path("corpus8"),
        "--input-dir",
        "-i",
        help=f"Input directory containing {globals.harness_ctx.context_type.__name__}"
        f" or { globals.harness_ctx.fixture_type.__name__ } messages",
    ),
    solana_shared_library: Path = typer.Option(
        Path("impl/lib/libsolfuzz_agave_v2.0.so"),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path("impl/lib/libsolfuzz_firedancer.so")],
        "--target",
        "-t",
        help="Shared object (.so) target file paths",
    ),
    output_dir: Path = typer.Option(
        Path("test_results"),
        "--output-dir",
        "-o",
        help="Output directory for test results",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    log_chunk_size: int = typer.Option(
        10000, "--chunk-size", "-c", help="Number of test results per file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output: log failed test cases",
    ),
    consensus_mode: bool = typer.Option(
        False,
        "--consensus-mode",
        "-c",
        help="Only fail on consensus failures. One such effect is to normalize error codes when comparing results",
    ),
    failures_only: bool = typer.Option(
        False,
        "--failures-only",
        "-f",
        help="Only log failed test cases",
    ),
    save_failures: bool = typer.Option(
        False,
        "--save-failures",
        "-sf",
        help="Saves failed test cases to results directory",
    ),
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library

    if consensus_mode:
        original_diff_effects_fn = globals.harness_ctx.diff_effect_fn

        def diff_effect_wrapper(a, b):
            if globals.harness_ctx.result_field_name:
                a_res = getattr(a, globals.harness_ctx.result_field_name)
                b_res = getattr(b, globals.harness_ctx.result_field_name)

                if not (a_res == 0 or b_res == 0):
                    # normalize error code. Modifies effects in place!
                    setattr(a, globals.harness_ctx.result_field_name, 1)
                    setattr(b, globals.harness_ctx.result_field_name, 1)
            else:
                print(
                    "No result field name found in harness context, will not normalize error codes."
                )

            for field in globals.harness_ctx.ignore_fields_for_consensus:
                try:
                    a.ClearField(field)
                except:
                    pass
                try:
                    b.ClearField(field)
                except:
                    pass

            return original_diff_effects_fn(a, b)

        globals.harness_ctx.diff_effect_fn = diff_effect_wrapper

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize shared libraries
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        globals.target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = globals.output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

    # Make failed protobuf directory
    if save_failures:
        failed_protobufs_dir = globals.output_dir / "failed_protobufs"
        failed_protobufs_dir.mkdir(parents=True, exist_ok=True)

    test_cases = list(input_dir.iterdir())
    num_test_cases = len(test_cases)

    # Process the test results in parallel
    print("Running tests...")
    test_case_results = []
    with Pool(
        processes=num_processes,
        initializer=initialize_process_output_buffers,
        initargs=(randomize_output_buffer,),
    ) as pool:
        for result in tqdm.tqdm(
            pool.imap(run_test, test_cases),
            total=num_test_cases,
        ):
            test_case_results.append(result)

    print("Logging results...")
    passed = 0
    failed = 0
    skipped = 0
    failed_tests = []
    skipped_tests = []
    target_log_files = {target: None for target in shared_libraries}
    for file_stem, status, stringified_results in test_case_results:
        if stringified_results is None:
            skipped += 1
            skipped_tests.append(file_stem)
            continue

        for target, string_result in stringified_results.items():
            if (passed + failed) % log_chunk_size == 0:
                if target_log_files[target]:
                    target_log_files[target].close()
                target_log_files[target] = open(
                    globals.output_dir / target.stem / (file_stem + ".txt"), "w"
                )

            if not failures_only or status == -1:
                target_log_files[target].write(
                    file_stem
                    + ":\n"
                    + string_result
                    + "\n"
                    + "-" * LOG_FILE_SEPARATOR_LENGTH
                    + "\n"
                )

        if status == 1:
            passed += 1
        elif status == -1:
            failed += 1
            failed_tests.append(file_stem)
            if save_failures:
                failed_protobufs = list(input_dir.glob(f"{file_stem}*"))
                for failed_protobuf in failed_protobufs:
                    shutil.copy(failed_protobuf, failed_protobufs_dir)

    print("Cleaning up...")
    for target in shared_libraries:
        if target_log_files[target]:
            target_log_files[target].close()
        globals.target_libraries[target].sol_compat_fini()

    peak_memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Peak Memory Usage: {peak_memory_usage_kb / 1024} MB")

    print(f"Total test cases: {passed + failed + skipped}")
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
    if verbose:
        print(f"Failed tests: {failed_tests}")
        print(f"Skipped tests: {skipped_tests}")


@app.command()
def decode_protobuf(
    input_dir: Path = typer.Option(
        Path("raw_instruction_context"),
        "--input-dir",
        "-i",
        help=f"Input directory containing {globals.harness_ctx.context_type.__name__} messages",
    ),
    output_dir: Path = typer.Option(
        Path("readable_instruction_context"),
        "--output-dir",
        "-o",
        help=f"Output directory for base58-encoded, human-readable {globals.harness_ctx.context_type.__name__} messages",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
):
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    num_test_cases = len(list(input_dir.iterdir()))

    write_results = []
    with Pool(processes=num_processes) as pool:
        for result in tqdm.tqdm(
            pool.imap(decode_single_test_case, input_dir.iterdir()),
            total=num_test_cases,
        ):
            write_results.append(result)

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")


if __name__ == "__main__":
    app()
