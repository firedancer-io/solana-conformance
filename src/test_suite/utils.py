import base58
import test_suite.invoke_pb2 as pb
import ctypes
from ctypes import c_uint64, c_int, POINTER
from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format


def decode_input(instruction_context: pb.InstrContext):
    """
    Decode any base58 fields of InstrContext in-place into bytes.

    Args:
        - instruction_context (pb.InstrContext): Instruction context (will be modified).
    """
    if instruction_context.program_id:
        instruction_context.program_id = base58.b58decode(instruction_context.program_id)
    if instruction_context.loader_id:
        instruction_context.loader_id = base58.b58decode(instruction_context.loader_id)

    for i in range(len(instruction_context.accounts)):
        if instruction_context.accounts[i].address:
            instruction_context.accounts[i].address = base58.b58decode(instruction_context.accounts[i].address)
        if instruction_context.accounts[i].data:
            instruction_context.accounts[i].data = base58.b58decode(instruction_context.accounts[i].data)
        if instruction_context.accounts[i].owner:
            instruction_context.accounts[i].owner = base58.b58decode(instruction_context.accounts[i].owner)

    if instruction_context.data:
        instruction_context.data = base58.b58decode(instruction_context.data)


def encode_input(instruction_context: pb.InstrContext):
    """
    Encode any base58 fields of InstrContext in-place into binary, digestable format.

    Args:
        - instruction_context (pb.InstrContext): Instruction context (will be modified).
    """
    if instruction_context.program_id:
        instruction_context.program_id = base58.b58encode(instruction_context.program_id)
    if instruction_context.loader_id:
        instruction_context.loader_id = base58.b58encode(instruction_context.loader_id)

    for i in range(len(instruction_context.accounts)):
        if instruction_context.accounts[i].address:
            instruction_context.accounts[i].address = base58.b58encode(instruction_context.accounts[i].address)
        if instruction_context.accounts[i].data:
            instruction_context.accounts[i].data = base58.b58encode(instruction_context.accounts[i].data)
        if instruction_context.accounts[i].owner:
            instruction_context.accounts[i].owner = base58.b58encode(instruction_context.accounts[i].owner)

    if instruction_context.data:
        instruction_context.data = base58.b58encode(instruction_context.data)


def encode_output(instruction_effects: pb.InstrEffects):
    """
    Encode any base58 fields of InstrEffects in-place into human-readable format.

    Args:
        - instruction_effects (pb.InstrEffects): Instruction effects (will be modified).
    """
    for i in range(len(instruction_effects.modified_accounts)):
        if instruction_effects.modified_accounts[i].address:
            instruction_effects.modified_accounts[i].address = base58.b58encode(instruction_effects.modified_accounts[i].address)
        if instruction_effects.modified_accounts[i].data:
            instruction_effects.modified_accounts[i].data = base58.b58encode(instruction_effects.modified_accounts[i].data)
        if instruction_effects.modified_accounts[i].owner:
            instruction_effects.modified_accounts[i].owner = base58.b58encode(instruction_effects.modified_accounts[i].owner)


def execute_single_library_on_single_test(target: str, serialized_instruction_context: str) -> str | None:
    """
    Execute a single target on a single test file containing an instruction context message.

    Args:
        - target (str): Target library name.
        - serialized_instruction_context (str): String-serialized instruction context message.

    Returns:
        - str | None: Serialized instruction effects, if they exist.
    """
    # Get the library corresponing to target
    library = globals.target_libraries[target]

    # Execute through each target library
    instruction_effects = process_instruction(library, serialized_instruction_context)

    return instruction_effects.SerializeToString(deterministic=True) if instruction_effects else None


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

    # Prepare input data
    in_data = serialized_instruction_context
    in_ptr = (ctypes.c_uint8 * len(in_data))(*in_data)
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(32 * 1024)  # Assume output size, adjust if necessary
    out_ptr = (ctypes.c_uint8 * out_sz.value)()

    # Call the function
    result = library.sol_compat_instr_execute_v1(out_ptr, ctypes.byref(out_sz), in_ptr, in_sz)

    # Result == 0 means execution failed
    if result == 0:
        return None

    # Process the output
    output_data = bytearray(out_ptr[:out_sz.value])
    output_object = pb.InstrEffects()
    output_object.ParseFromString(output_data)

    return output_object


def generate_test_cases(test_file: Path) -> tuple[Path, str]:
    """
    Reads in test files and generates Protobuf objects for each test case.

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


def process_single_test_case(execution_context: tuple[Path, str]):
    """
    Process a single execution context (file, serialized instruction context) through
    all target libraries and returns serialized instruction effects. This
    function is called by processes.

    Args:
        - execution_context (tuple[Path, str]): Tuple of file and serialized instruction context.

    Returns:
        - tuple[str, dict[str, str | None] | None]: Tuple of file stem and dictionary of target library names
            and instruction effects.
    """
    file, serialized_instruction_context = execution_context

    # Mark as skipped if instruction context doesn't exist
    if serialized_instruction_context is None:
        return file.stem, None

    # Execute test case on each target library
    results = {}
    for target in globals.target_libraries:
        result = execute_single_library_on_single_test(target, serialized_instruction_context)
        results[target] = result

    return file.stem, results


def build_test_results(execution_result: tuple[Path, dict[str, str | None]]):
    """
    Builds the results of test execution and return a dictionary of results per file and per target.

    Args:
        - execution_result (tuple[Path, dict[str, str | None] | None]): Tuple of file and target results.

    Returns:

    """
    file_stem, results = execution_result
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
