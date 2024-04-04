from collections import Counter
from typing import List
import typer
import ctypes
from multiprocessing import Pool
from pathlib import Path
from google.protobuf import text_format
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
import test_suite.invoke_pb2 as pb
from test_suite.codec_utils import encode_input
from test_suite.multiprocessing_utils import (
    check_consistency_in_results,
    generate_test_case,
    initialize_process_output_buffers,
    merge_results_over_iterations,
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
def debug_instruction(
    file: Path = typer.Option(None, "--input", "-i", help="Input file"),
    shared_library: Path = typer.Option(
        Path("impl/firedancer/build/native/clang/lib/libfd_exec_sol_compat.so"),
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
def consolidate_logs(
    input_dir: Path = typer.Option(
        Path("test_results"),
        "--input-dir",
        "-i",
        help="Input directory containing test results",
    ),
    output_dir: Path = typer.Option(
        Path("consolidated_logs"),
        "--output-dir",
        "-o",
        help="Output directory for consolidated logs",
    ),
    chunk_size: int = typer.Option(
        10000, "--chunk-size", "-c", help="Number of test results per file"
    ),
):
    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through each library
    for lib_dir in filter(lambda x: x.is_dir(), input_dir.iterdir()):
        # Make the lib output directory
        lib = lib_dir.stem
        (output_dir / lib).mkdir(parents=True, exist_ok=True)

        # Grab all log files
        log_files = sorted(list(lib_dir.glob("*.txt")))

        current_log_file = None

        for i in range(len(log_files)):
            # Open a new log file every chunk_size test cases
            if i % chunk_size == 0:
                if current_log_file:
                    current_log_file.close()
                current_log_file = open(
                    output_dir / lib / f"{log_files[i].stem}.txt", "w"
                )

            # Write test case name + log contents + separators
            current_log_file.write(log_files[i].stem + ":\n")
            current_log_file.write(log_files[i].read_text())
            current_log_file.write("\n" + "-" * LOG_FILE_SEPARATOR_LENGTH + "\n")

        if current_log_file:
            current_log_file.close()


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
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library

    # Create the output directory, if necessary
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    # Keep track of how many files were (un)successfully written
    written = 0
    total = 0

    # Iterate through each binary-encoded message
    for file in input_dir.iterdir():
        total += 1
        _, serialized_instruction_context = generate_test_case(file)

        # Skip if input is invalid
        if serialized_instruction_context is None:
            if verbose:
                print(f"Could not validate message: {file.stem}")
            continue

        # Encode the input fields to be human readable
        instruction_context = pb.InstrContext()
        instruction_context.ParseFromString(serialized_instruction_context)
        encode_input(instruction_context)

        with open(output_dir / file.name, "w") as f:
            f.write(
                text_format.MessageToString(
                    instruction_context, print_unknown_fields=False
                )
            )
        written += 1

        # Validate the binary and human-readable messages are the same
        if check_decode_results:
            readable_instruction_context = text_format.Parse(
                (output_dir / file.name).read_text(), pb.InstrContext()
            )
            assert readable_instruction_context == instruction_context, file.name

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{total} total files seen")
    print(f"{written} files successfully written")


if __name__ == "__main__":
    app()
