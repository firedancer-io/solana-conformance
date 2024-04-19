from collections import Counter
import shutil
from typing import List
import typer
import ctypes
from multiprocessing import Pool
from pathlib import Path
from google.protobuf import text_format
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
import test_suite.invoke_pb2 as pb
from test_suite.codec_utils import encode_input, encode_output
from test_suite.multiprocessing_utils import (
    check_consistency_in_results,
    decode_single_test_case,
    generate_test_case,
    initialize_process_output_buffers,
    merge_results_over_iterations,
    process_instruction,
    process_single_test_case,
    build_test_results,
)
import test_suite.globals as globals
from test_suite.debugger import debug_host
import resource


app = typer.Typer(
    help="Validate instruction effects from clients using instruction context Protobuf messages."
)


@app.command()
def execute_single_instruction(
    file: Path = typer.Option(None, "--input", "-i", help="Input file"),
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
    _, instruction_context = generate_test_case(file)
    assert instruction_context is not None, f"Unable to read {file.name}"

    # Initialize output buffers and shared library
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)
    lib = ctypes.CDLL(shared_library)
    lib.sol_compat_init()

    # Execute and cleanup
    instruction_effects = process_instruction(lib, instruction_context)
    lib.sol_compat_fini()

    # Print human-readable output
    if instruction_effects:
        encode_output(instruction_effects)

    print(instruction_effects)


@app.command()
def debug_instruction(
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
    _, instruction_context = generate_test_case(file)
    assert instruction_context is not None, f"Unable to read {file.name}"
    debug_host(shared_library, instruction_context, gdb=debugger)


@app.command()
def check_consistency(
    input_dir: Path = typer.Option(
        Path("corpus8"),
        "--input-dir",
        "-i",
        help="Input directory containing instruction context messages",
    ),
    shared_libraries: List[Path] = typer.Option(
        [], "--target", "-t", help="Shared object (.so) target file paths"
    ),
    output_dir: Path = typer.Option(
        Path("consistency_results"),
        "--output-dir",
        "-o",
        help="Output directory for test results",
    ),
    num_iterations: int = typer.Option(
        2,
        "--num-iterations",
        "-n",
        help="Number of consistency iterations to run for each library",
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
):
    # Initialize globals
    globals.output_dir = output_dir
    globals.n_iterations = num_iterations

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate the test cases in parallel from files on disk
    print("Reading test files...")
    with Pool(processes=num_processes) as pool:
        execution_contexts = pool.map(generate_test_case, input_dir.iterdir())

    results_per_iteration = []
    for iteration in range(globals.n_iterations):
        print(f"Starting iteration {iteration}...")

        # Use the target libraries global map to store shared libraries
        for target in shared_libraries:
            lib = ctypes.CDLL(target)
            lib.sol_compat_init()
            globals.target_libraries[target] = lib

            # Initialize the libraries for each iteration
            for iteration in range(globals.n_iterations):
                # Make output directory
                (globals.output_dir / target.stem / str(iteration)).mkdir(
                    parents=True, exist_ok=True
                )

        # Process the test cases in parallel through shared libraries for n interations
        print("Executing tests...")
        with Pool(
            processes=num_processes,
            initializer=initialize_process_output_buffers,
            initargs=(randomize_output_buffer,),
        ) as pool:
            execution_results = pool.starmap(
                process_single_test_case, execution_contexts
            )
            results_per_iteration.append(execution_results)

        print("Cleaning up...")
        for target in shared_libraries:
            globals.target_libraries[target].sol_compat_fini()

    # Build the results properly
    with Pool(processes=num_processes) as pool:
        execution_results = pool.map(
            merge_results_over_iterations, zip(*results_per_iteration)
        )

    # Process the test results in parallel
    print("Building test results...")
    with Pool(processes=num_processes) as pool:
        test_case_results = pool.starmap(
            check_consistency_in_results, execution_results
        )

    # Compute per-library results
    library_results = {}
    for library in globals.target_libraries:
        library_results[library] = {"passed": 0, "failed": 0, "skipped": 0}

    # Build the results
    for result in test_case_results:
        for library, outcome in result.items():
            library_results[library]["passed"] += outcome == 1
            library_results[library]["failed"] += outcome == -1
            library_results[library]["skipped"] += outcome == 0

    peak_memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Peak Memory Usage: {peak_memory_usage_kb / 1024} MB")

    print("-" * LOG_FILE_SEPARATOR_LENGTH)

    for library in globals.target_libraries:
        results = library_results[library]
        print(f"{library} results")
        print(f"Total test cases: {sum(results.values())}")
        print(
            f"Passed: {results['passed']}, Failed: {results['failed']}, Skipped: {results['skipped']}"
        )
        print("-" * LOG_FILE_SEPARATOR_LENGTH)


@app.command()
def run_tests(
    input_dir: Path = typer.Option(
        Path("corpus8"),
        "--input-dir",
        "-i",
        help="Input directory containing instruction context messages",
    ),
    solana_shared_library: Path = typer.Option(
        Path("impl/lib/libsolfuzz_agave_v2.0.so"),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [], "--target", "-t", help="Shared object (.so) target file paths"
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
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library

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

    # Generate the test cases in parallel from files on disk
    print("Reading test files...")
    with Pool(processes=num_processes) as pool:
        execution_contexts = pool.map(generate_test_case, input_dir.iterdir())

    # Process the test cases in parallel through shared libraries
    print("Executing tests...")
    with Pool(
        processes=num_processes,
        initializer=initialize_process_output_buffers,
        initargs=(randomize_output_buffer,),
    ) as pool:
        execution_results = pool.starmap(process_single_test_case, execution_contexts)

    # Process the test results in parallel
    print("Building test results...")
    with Pool(processes=num_processes) as pool:
        test_case_results = pool.starmap(build_test_results, execution_results)
        counts = Counter(test_case_results)
        passed = counts[1]
        failed = counts[-1]
        skipped = counts[0]

    print("Logging results...")
    counter = 0
    target_log_files = {target: None for target in shared_libraries}
    for file, result in execution_results:
        if result is None:
            continue

        for target, serialized_instruction_effects in result.items():
            if counter % log_chunk_size == 0:
                if target_log_files[target]:
                    target_log_files[target].close()
                target_log_files[target] = open(
                    globals.output_dir / target.stem / (file + ".txt"), "w"
                )

            target_log_files[target].write(file + ":\n")

            if serialized_instruction_effects is None:
                target_log_files[target].write(str(None))
            else:
                instruction_effects = pb.InstrEffects()
                instruction_effects.ParseFromString(serialized_instruction_effects)
                encode_output(instruction_effects)
                target_log_files[target].write(
                    text_format.MessageToString(instruction_effects)
                )
            target_log_files[target].write(
                "\n" + "-" * LOG_FILE_SEPARATOR_LENGTH + "\n"
            )
        counter += 1

    for target in shared_libraries:
        if target_log_files[target]:
            target_log_files[target].close()

    print("Cleaning up...")
    for target in shared_libraries:
        globals.target_libraries[target].sol_compat_fini()

    peak_memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Peak Memory Usage: {peak_memory_usage_kb / 1024} MB")

    print(f"Total test cases: {passed + failed + skipped}")
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")


@app.command()
def decode_protobuf(
    input_dir: Path = typer.Option(
        Path("raw_instruction_context"),
        "--input-dir",
        "-i",
        help="Input directory containing instruction context messages in binary format",
    ),
    output_dir: Path = typer.Option(
        Path("readable_instruction_context"),
        "--output-dir",
        "-o",
        help="Output directory for base58-encoded, human-readable instruction context messages",
    ),
    check_decode_results: bool = typer.Option(
        False,
        "--check-results",
        "-c",
        help="Validate binary and human readable messages are identical",
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

    with Pool(processes=num_processes) as pool:
        write_results = pool.map(decode_single_test_case, input_dir.iterdir())

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")


if __name__ == "__main__":
    app()
