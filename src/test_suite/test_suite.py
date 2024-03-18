from typing import List
import typer
import ctypes

from pathlib import Path
from google.protobuf import text_format
import test_suite.invoke_pb2 as pb

from test_suite.utils import process_instruction

app = typer.Typer(help="Computes Solana instruction effects from plaintext instruction context protobuf messages.")

@app.command()
def run_tests(
    input_dir: Path = typer.Option(
        Path("instruction_context"),
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


if __name__ == "__main__":
    app()
