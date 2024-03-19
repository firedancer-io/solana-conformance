import base58
from typing import List
import typer
import ctypes

from pathlib import Path
from google.protobuf import text_format
import test_suite.invoke_pb2 as pb

from test_suite.utils import process_instruction, decode_input, encode_input

LOG_FILE_SEPARATOR_LENGTH = 20

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
        Path("libsolfuzz_agave.so"),
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
    )
):
    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    passed = 0
    failed = 0
    skipped = 0

    # Load in and initialize shared libraries
    target_libraries = {}
    for target in [solana_shared_library] + shared_libraries:
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through input messages
    for file in input_dir.iterdir():
        # Read in human-readable Protobuf messages
        with open(file) as f:
            instruction_context = text_format.Parse(f.read(), pb.InstrContext())

        # Decode base58 encoded, human-readable fields
        decode_input(instruction_context)

        # Capture results from each target
        execution_results = {}

        for target, lib in target_libraries.items():
            # Fetch result through shared library
            result = process_instruction(lib, instruction_context)
            execution_results[target] = result

        # Skip the test case if the input is invalid
        if execution_results[solana_shared_library] is None:
            skipped += 1
            continue

        # Log execution results
        for target, result in execution_results.items():
            with open(output_dir / target.stem / (file.name + ".txt"), "w") as f:
                f.write(str(result))

        # Compare results
        test_case_passed = all(result == execution_results[solana_shared_library] for result in execution_results.values())

        if test_case_passed:
            passed += 1
        else:
            failed += 1

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
            with open(output_dir / file.name, "w") as f:
                f.write(instruction_context.__str__())
        except Exception as e:
            print(f"Could not read {file.stem}: {e}")


if __name__ == "__main__":
    app()
