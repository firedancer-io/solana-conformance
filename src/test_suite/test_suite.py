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
    input_folder: Path = typer.Option(
        Path("instruction_context"),
        "--input-folder",
        "-i",
        help="Input folder containing instruction context messages in human-readable format"
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):
    passed = 0
    failed = 0
    skipped = 0

    file1 = open("solana.txt", "w")
    file2 = open("firedancer.txt", "w")

    # Load in and initialize shared libraries
    libraries = []
    for target in [solana_shared_library] + shared_libraries:
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        libraries.append(lib)

    # Iterate through input messages
    for file in input_folder.iterdir():
        with open(file) as f:
            # Read in human-readable Protobuf messages
            instruction_context = text_format.Parse(f.read(), pb.InstrContext())

        # Fetch ground truth through Solana program
        ground_truth_result = process_instruction(libraries[0], instruction_context)

        if ground_truth_result == None:
            skipped += 1
            continue

        # Iterate through shared libraries and get results
        results = []
        for lib in libraries[1:]:
            # Fetch result through shared library
            result = process_instruction(lib, instruction_context)
            results.append(result)

        # Compare results
        test_case_passed = all(result == ground_truth_result for result in results)

        if test_case_passed:
            passed += 1
        else:
            file1.write(str(result) + f"-{passed}-"*20 + "\n")
            file2.write(str(ground_truth_result) + "-"*20 + "\n")
            failed += 1

    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")


    file1.close()
    file2.close()


if __name__ == "__main__":
    app()
