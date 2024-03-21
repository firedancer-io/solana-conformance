import time
from typing import List
import typer
import ctypes
from multiprocessing import Queue, Value
import queue
from pathlib import Path
from google.protobuf import text_format
import test_suite.invoke_pb2 as pb

from test_suite.utils import decode_input, encode_input, start_process
from test_suite.globals import target_libraries

LOG_FILE_SEPARATOR_LENGTH = 20
NUM_PROCESSES = 8
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
    ),
    use_binary: bool = typer.Option(
        False,
        "--use-binary",
        "-b",
        help="Enable if using standard Protobuf binary-encoded instruction context messages"
    )
):
    # Specify globals
    global target_libraries

    # Create the output directory, if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    passed = 0
    failed = 0
    skipped = 0

    # Load in and initialize shared libraries
    for target in [solana_shared_library] + shared_libraries:
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

    # Load in context for instruction execution
    execution_contexts = []

    # Iterate through input messages
    for file in input_dir.iterdir():
        # Optionally read in binary-encoded Protobuf messages
        try:
            if use_binary:
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
            execution_contexts.append((file, instruction_context.SerializeToString()))
        except:
            # Unable to read message, skip and continue
            skipped += 1
            continue

    execution_contexts += [None] * NUM_PROCESSES

    execution_results_per_file = {}  # file -> target -> execution result
    for target in target_libraries:
        # For process health monitoring
        last_response = [Value(ctypes.c_uint32, int(time.time())) for _ in range(NUM_PROCESSES)]

        processes = [None for _ in range(NUM_PROCESSES)]
        processes_finished = [False for _ in range(NUM_PROCESSES)]
        current_context_index = 0
        target_results = []

        task_queue = Queue()
        result_queue = Queue()

        while not all(processes_finished):
            print(current_context_index, "/", len(execution_contexts))
            for i in range(NUM_PROCESSES):
                # Skip over this process if its already done
                if processes_finished[i]: continue

                # Case 1: Process does not exist / is already killed
                # Create a new process and result queue
                if processes[i] is None:
                    # Avoid spinning up new processes if there are no more tasks
                    if current_context_index >= len(execution_contexts):
                        processes_finished[i] = True
                        continue

                    # Add a new task to the queue
                    task_queue.put(execution_contexts[current_context_index])
                    current_context_index += 1

                    # Update heartbeat time
                    with last_response[i].get_lock():
                        last_response[i].value = int(time.time())


                    processes[i] = start_process(target, task_queue, result_queue, last_response[i])
                    continue

                # Case 2: Process has a result available
                # Take the result and add a new task to the queue
                try:
                    result = result_queue.get_nowait()

                    if result == None:
                        # Lol Python multiprocessing is so dumb - queues have to be emptied before the process
                        # can be joined, so I'm terminating the process since we don't need it anymore and
                        # to avoid deadlock
                        processes_finished[i] = True
                        processes[i].terminate()
                        processes[i].join()
                        continue

                    target_results.append(result)
                    task_queue.put(execution_contexts[current_context_index])
                    current_context_index += 1
                except queue.Empty:
                    pass

                # Case 3: Process is not responsive
                # Kill the process
                current_time = time.time()
                with last_response[i].get_lock():
                    last_response_time = last_response[i].value
                if current_time - last_response_time > PROCESS_TIMEOUT:
                    processes[i].terminate()
                    processes[i].join()
                    processes[i] = None
                    continue

                # If it gets down here, the process is still running as normal

        for file_name, serialized_instruction_effects in target_results:
            if file_name not in execution_results_per_file:
                execution_results_per_file[file_name] = {}

            if serialized_instruction_effects is None:
                instruction_effects = None
            else:
                instruction_effects = pb.InstrEffects()
                instruction_effects.ParseFromString(serialized_instruction_effects)

            # Store the execution results for each file-target pair
            execution_results_per_file[file_name][target] = instruction_effects

    for file_name, target_results in execution_results_per_file.items():
        # Skip the test case if Solana couldn't process the input
        if solana_shared_library not in target_results or target_results[solana_shared_library] is None:
            skipped += 1
            continue

        # Log execution results
        for target, result in target_results.items():
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
            with open(output_dir / file.name, "w") as f:
                f.write(instruction_context.__str__())
        except Exception as e:
            print(f"Could not read {file.stem}: {e}")


if __name__ == "__main__":
    app()
