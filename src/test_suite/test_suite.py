from collections import Counter
from typing import List
import typer
import ctypes
from multiprocessing import Pool
from pathlib import Path
from google.protobuf import text_format
import test_suite.invoke_pb2 as pb
from test_suite.utils import encode_input, generate_test_cases, process_single_test_case, build_test_results
import test_suite.globals as globals
import resource

LOG_FILE_SEPARATOR_LENGTH = 20
PROCESS_TIMEOUT = 30

app = typer.Typer(help="Computes Solana instruction effects from plaintext instruction context protobuf messages.")


@app.command()
def consolidate_logs(
    input_dir: Path = typer.Option(
        Path("test_results"),
        "--input-dir",
        "-i",
        help="Input directory containing test results"
    ),
    output_dir: Path = typer.Option(
        Path("consolidated_logs"),
        "--output-dir",
        "-o",
        help="Output directory for consolidated logs"
    ),
    chunk_size: int = typer.Option(
        10000,
        "--chunk-size",
        "-c",
        help="Number of test results per file"
    )
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
                if current_log_file: current_log_file.close()
                current_log_file = open(output_dir / lib / f"{log_files[i].stem}.txt", "w")

            # Write test case name + log contents + separators
            current_log_file.write(log_files[i].stem + ":\n")
            current_log_file.write(log_files[i].read_text())
            current_log_file.write("\n" + "-"*LOG_FILE_SEPARATOR_LENGTH + "\n")

        if current_log_file: current_log_file.close()


@app.command()
def run_tests(
    input_dir: Path = typer.Option(
        Path("readable_instruction_context"),
        "--input-dir",
        "-i",
        help="Input directory containing instruction context messages in human-readable format"
    ),
    solana_shared_library: Path = typer.Option(
        Path("impl/lib/libsolfuzz_agave.so.2.0"),
        "--solana-target",
        "-s",
        help="Solana shared object (.so) target file path"
    ),
    shared_libraries: List[Path] = typer.Option(
        [],
        "--target",
        "-t",
        help="Shared object (.so) target file paths"
    ),
    output_dir: Path = typer.Option(
        Path("test_results"),
        "--output-dir",
        "-o",
        help="Output directory for test results"
    ),
    num_processes: int = typer.Option(
        4,
        "--num-processes",
        "-n",
        help="Number of processes to use"
    )
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals and initialize the libraries
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        globals.target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate the test cases in parallel from files on disk
    print("Reading test files...")
    with Pool(processes=num_processes) as pool:
        execution_contexts = list(pool.imap_unordered(generate_test_cases, input_dir.iterdir()))

    # Process the test cases in parallel through shared libraries
    print("Executing tests...")
    with Pool(processes=num_processes) as pool:
        execution_results = list(pool.imap_unordered(process_single_test_case, execution_contexts))

    # Process the test results in parallel
    print("Building test results...")
    with Pool(processes=num_processes) as pool:
        test_case_results = pool.imap_unordered(build_test_results, execution_results)
        counts = Counter(test_case_results)
        passed = counts[1]
        failed = counts[-1]
        skipped = counts[0]

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
        help="Input directory containing instruction context messages in binary format"
    ),
    output_dir: Path = typer.Option(
        Path("readable_instruction_context"),
        "--output-dir",
        "-o",
        help="Output directory for base58-encoded, human-readable instruction context messages"
    )
):
    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through each binary-encoded message
    for file in input_dir.iterdir():
        try:
            instruction_context = pb.InstrContext()

            # Read in the message
            with open(file, "rb") as f:
                content = f.read()
                instruction_context.ParseFromString(content)

            # Encode bytes fields into base58
            encode_input(instruction_context)

            # Output the human-readable message
            text = text_format.MessageToString(instruction_context)
            if len(text) > 0:
                with open(output_dir / file.name, "w") as f:
                    f.write(text)
        except Exception as e:
            print(f"Could not read {file.stem}: {e}")


if __name__ == "__main__":
    app()
