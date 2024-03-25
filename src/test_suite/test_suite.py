from typing import List
import typer
import ctypes
from multiprocessing import Queue
from pathlib import Path
from google.protobuf import text_format
import test_suite.invoke_pb2 as pb

from test_suite.utils import decode_input, encode_input, start_process
from test_suite.globals import target_libraries

LOG_FILE_SEPARATOR_LENGTH = 20
NUM_PROCESSES = 4
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
    use_binary: bool = typer.Option(
        False,
        "--use-binary",
        "-b",
        help="Enable if using standard Protobuf binary-encoded instruction context messages"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):
    # Specify globals
    global target_libraries

    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Statistic tracking
    passed = 0
    failed = 0
    skipped = 0

    # Load in context for instruction execution
    execution_contexts = []

    # Iterate through input messages
    for file in input_dir.iterdir():
        # Optionally read in binary-encoded Protobuf messages
        try:
            if use_binary:
                # Read in binary Protobuf messages
                with open(file, "rb") as f:
                    instruction_context = pb.InstrContext()
                    instruction_context.ParseFromString(f.read())
            else:
                # Read in human-readable Protobuf messages
                with open(file) as f:
                    instruction_context = text_format.Parse(f.read(), pb.InstrContext())

                # Decode base58 encoded, human-readable fields
                decode_input(instruction_context)

            # Serialize instruction context to string (pickleable)
            execution_contexts.append((file, instruction_context.SerializeToString(deterministic=True)))
        except KeyboardInterrupt:
            # Handle CTRL-C
            return
        except:
            # Unable to read message, skip and continue
            skipped += 1
            continue

    execution_results_per_file = {}  # file -> target -> execution result
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

        # Keep track of which tasks we've completed and which results we've received
        tasks_queue = Queue()
        results_queue = Queue()
        target_results = []

        # Add tasks to queue
        for task in execution_contexts:
            tasks_queue.put(task)

        # Add sentinel values to signal end of tasks
        for _ in range(NUM_PROCESSES):
            tasks_queue.put(None)

        # Keep track of which processes are spun up and finished
        processes = [start_process(target, tasks_queue, results_queue) for _ in range(NUM_PROCESSES)]

        # Read results until all processes finish tasks
        num_nones = 0
        num_tests_finished = 0
        while num_nones < NUM_PROCESSES:
            # Read a result from the queue
            result = results_queue.get()
            if result is None:
                num_nones += 1
                continue

            num_tests_finished += 1
            if verbose: print(f"Finished running {num_tests_finished} / {len(execution_contexts)} tasks for {target.stem}")
            target_results.append(result)

        # Join all processes
        for process in processes:
            process.join()

        # Build results per file and per target
        for file_name, serialized_instruction_effects in target_results:
            if file_name not in execution_results_per_file:
                execution_results_per_file[file_name] = {}

            # Read the serialized output message if it exists
            if serialized_instruction_effects is None:
                instruction_effects = None
            else:
                instruction_effects = pb.InstrEffects()
                instruction_effects.ParseFromString(serialized_instruction_effects)

            # Store the execution results for each file-target pair
            execution_results_per_file[file_name][target] = instruction_effects

    for file_name, target_results in execution_results_per_file.items():
        # Log execution results
        for target in shared_libraries:
            # Library did not respond here, could be a terminated process
            if target not in target_results:
                target_results[target] = None

            with open(output_dir / target.stem / (file_name + ".txt"), "w") as f:
                f.write(str(result))

        # Compare results
        test_case_passed = all(result == target_results[solana_shared_library] for result in target_results.values())

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
            text = text_format.MessageToString(instruction_context)
            if len(text) > 0:
                with open(output_dir / file.name, "w") as f:
                    f.write(text)
        except Exception as e:
            print(f"Could not read {file.stem}: {e}")


if __name__ == "__main__":
    app()
