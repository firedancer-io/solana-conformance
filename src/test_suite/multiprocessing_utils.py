from test_suite.constants import OUTPUT_BUFFER_SIZE
import test_suite.invoke_pb2 as pb
from test_suite.codec_utils import encode_output, decode_input
import ctypes
from ctypes import c_uint64, c_int, POINTER
from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format
import os


def process_instruction(
    library: ctypes.CDLL,
    serialized_instruction_context: str
) -> pb.InstrEffects | None:
    """
    Process an instruction through a provided shared library and return the result.

    Args:
        - library (ctypes.CDLL): Shared library to process instructions.
        - serialized_instruction_context (str): Serialized instruction context message.

    Returns:
        - pb.InstrEffects | None: Result of instruction execution.
    """

    # Define argument and return types
    library.sol_compat_instr_execute_v1.argtypes = [
        POINTER(ctypes.c_uint8),  # out_ptr
        POINTER(c_uint64),        # out_psz
        POINTER(ctypes.c_uint8),  # in_ptr
        c_uint64                  # in_sz
    ]
    library.sol_compat_instr_execute_v1.restype = c_int

    # Prepare input data and output buffers
    in_data = serialized_instruction_context
    in_ptr = (ctypes.c_uint8 * len(in_data))(*in_data)
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(OUTPUT_BUFFER_SIZE)

    # Call the function
    result = library.sol_compat_instr_execute_v1(globals.output_buffer_pointer, ctypes.byref(out_sz), in_ptr, in_sz)

    # Result == 0 means execution failed
    if result == 0:
        return None

    # Process the output
    output_data = bytearray(globals.output_buffer_pointer[:out_sz.value])
    output_object = pb.InstrEffects()
    output_object.ParseFromString(output_data)

    return output_object


def generate_test_case(test_file: Path) -> tuple[Path, str | None]:
    """
    Reads in test files and generates a Protobuf object for a test case.

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - tuple[Path, str | None]: Tuple of file and serialized instruction context, if exists.
    """
    # Try to read in first as binary-encoded Protobuf messages
    try:
        # Read in binary Protobuf messages
        with open(test_file, "rb") as f:
            instruction_context = pb.InstrContext()
            instruction_context.ParseFromString(f.read())
    except:
        try:
            # Maybe it's in human-readable Protobuf format?
            with open(test_file) as f:
                instruction_context = text_format.Parse(f.read(), pb.InstrContext())

            # Decode base58 encoded, human-readable fields
            decode_input(instruction_context)
        except:
            # Unable to read message, skip and continue
            instruction_context = None

    if instruction_context is None:
        # Unreadable file, skip it
        return test_file, None

    # Serialize instruction context to string (pickleable)
    return test_file, instruction_context.SerializeToString(deterministic=True)


def process_single_test_case(file: Path, serialized_instruction_context: str | None) -> tuple[str, dict[str, str | None] | None]:
    """
    Process a single execution context (file, serialized instruction context) through
    all target libraries and returns serialized instruction effects. This
    function is called by processes.

    Args:
        - file (Path): File containing serialized instruction context.
        - serialized_instruction_context (str | None): Serialized instruction context.

    Returns:
        - tuple[str, dict[str, str | None] | None]: Tuple of file stem and dictionary of target library names
            and instruction effects.
    """
    # Mark as skipped if instruction context doesn't exist
    if serialized_instruction_context is None:
        return file.stem, None

    # Execute test case on each target library
    results = {}
    for target in globals.target_libraries:
        instruction_effects = process_instruction(globals.target_libraries[target], serialized_instruction_context)
        result = instruction_effects.SerializeToString(deterministic=True) if instruction_effects else None
        results[target] = result

    return file.stem, results


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


def check_consistency_in_results(file_stem: Path, results: dict) -> dict[str, bool]:
    """
    Check consistency for all target libraries over all iterations for a test case.

    Args:
        - file_stem (Path): File stem of the test case.
        - execution_results (dict): Dictionary of target library names and serialized instruction effects.

    Returns:
        - dict[str, bool]: For each target name, 1 if passed, -1 if failed, 0 if skipped.
    """
    if results is None:
        return {target: 0 for target in globals.target_libraries}

    results_per_target = {}
    for target in globals.target_libraries:
        protobuf_structures = {}
        for iteration in range(globals.n_iterations):
            # Create a Protobuf struct to compare and output, if applicable
            protobuf_struct = None
            if results[target][iteration]:
                # Turn bytes into human readable fields
                protobuf_struct = pb.InstrEffects()
                protobuf_struct.ParseFromString(results[target][iteration])
                encode_output(protobuf_struct)

            protobuf_structures[iteration] = protobuf_struct

            # Write output Protobuf struct to logs
            with open(globals.output_dir / target.stem / str(iteration) / (file_stem + ".txt"), "w") as f:
                if protobuf_struct:
                    f.write(text_format.MessageToString(protobuf_struct))
                else:
                    f.write(str(None))

        test_case_passed = all(protobuf_structures[iteration] == protobuf_structures[0] for iteration in range(globals.n_iterations))
        results_per_target[target] = 1 if test_case_passed else -1

    return results_per_target


def build_test_results(file_stem: Path, results: dict[str, str | None]) -> int:
    """
    Build a single result of single test execution and returns whether the test passed or failed.

    Args:
        - file_stem (Path): File stem of the test case.
        - results (dict[str, str | None]): Dictionary of target library names and serialized instruction effects.

    Returns:
        - int: 1 if passed, -1 if failed, 0 if skipped.
    """
    if results is None:
        # Mark as skipped (0)
        return 0

    # Log execution results
    protobuf_structures = {}
    for target, result in results.items():
        # Create a Protobuf struct to compare and output, if applicable
        protobuf_struct = None
        if result:
            # Turn bytes into human readable fields
            protobuf_struct = pb.InstrEffects()
            protobuf_struct.ParseFromString(result)
            encode_output(protobuf_struct)

        protobuf_structures[target] = protobuf_struct

        # Write output Protobuf struct to logs
        with open(globals.output_dir / target.stem / (file_stem + ".txt"), "w") as f:
            if protobuf_struct:
                f.write(text_format.MessageToString(protobuf_struct))
            else:
                f.write(str(None))

    test_case_passed = all(protobuf_structures[globals.solana_shared_library] == result for result in protobuf_structures.values())

    # 1 = passed, -1 = failed
    return 1 if test_case_passed else -1


def initialize_process_output_buffers(randomize_output_buffer = False):
    """
    Initialize shared memory and pointers for output buffers for each process.

    Args:
        - randomize_output_buffer (bool): Whether to randomize output buffer.
    """
    globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)()

    if randomize_output_buffer:
        output_buffer_random_bytes = os.urandom(OUTPUT_BUFFER_SIZE)
        globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)(*output_buffer_random_bytes)
