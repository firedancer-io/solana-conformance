import base58
import test_suite.invoke_pb2 as pb
import ctypes
from ctypes import c_uint64, c_int, POINTER
from google.protobuf import text_format
from pathlib import Path
from test_suite.globals import target_libraries
from itertools import repeat
from multiprocessing import Pool

def decode_input(instruction_context: pb.InstrContext):
    """
    Decode any base58 fields of InstrContext in-place into bytes.

    Args:
        - instruction_context (pb.InstrContext): Instruction context (will be modified).
    """
    instruction_context.program_id = base58.b58decode(instruction_context.program_id)
    instruction_context.loader_id = base58.b58decode(instruction_context.loader_id)

    for i in range(len(instruction_context.accounts)):
        instruction_context.accounts[i].address = base58.b58decode(instruction_context.accounts[i].address)
        instruction_context.accounts[i].data = base58.b58decode(instruction_context.accounts[i].data)
        instruction_context.accounts[i].owner = base58.b58decode(instruction_context.accounts[i].owner)

    instruction_context.data = base58.b58decode(instruction_context.data)


def encode_input(instruction_context: pb.InstrContext):
    """
    Encode any base58 fields of InstrContext in-place into binary, digestable format.

    Args:
        - instruction_context (pb.InstrContext): Instruction context (will be modified).
    """
    instruction_context.program_id = base58.b58encode(instruction_context.program_id)
    instruction_context.loader_id = base58.b58encode(instruction_context.loader_id)

    for i in range(len(instruction_context.accounts)):
        instruction_context.accounts[i].address = base58.b58encode(instruction_context.accounts[i].address)
        instruction_context.accounts[i].data = base58.b58encode(instruction_context.accounts[i].data)
        instruction_context.accounts[i].owner = base58.b58encode(instruction_context.accounts[i].owner)

    instruction_context.data = base58.b58encode(instruction_context.data)


def encode_output(instruction_effects: pb.InstrEffects):
    """
    Encode any base58 fields of InstrEffects in-place into human-readable format.

    Args:
        - instruction_effects (pb.InstrEffects): Instruction effects (will be modified).
    """
    for i in range(len(instruction_effects.modified_accounts)):
        instruction_effects.modified_accounts[i].address = base58.b58encode(instruction_effects.modified_accounts[i].address)
        instruction_effects.modified_accounts[i].data = base58.b58encode(instruction_effects.modified_accounts[i].data)
        instruction_effects.modified_accounts[i].owner = base58.b58encode(instruction_effects.modified_accounts[i].owner)


def execute_single_library_on_single_test(target: str, file: Path, serialized_instruction_context: str) -> tuple[str, str | None]:
    """
    Execute a single target on a single test file containing an instruction context message.

    Args:
        - target (str): Target library name.
        - file (Path): Path to instruction context message.
        - serialized_instruction_context (str): String-serialized instruction context message.

    Returns:
        - tuple[str, str | None]: Test file name serialized instruction effects.
    """
    global target_libraries

    # Get the library corresponing to target
    library = target_libraries[target]

    # Deserialize instruction context message
    instruction_context = pb.InstrContext()
    instruction_context.ParseFromString(serialized_instruction_context)

    # Execute through each target library
    instruction_effects = process_instruction(library, instruction_context)

    return file.stem, instruction_effects.SerializeToString() if instruction_effects else None


def process_instruction(
    library: ctypes.CDLL,
    instruction_context: pb.InstrContext
) -> pb.InstrEffects | None:
    """
    Process an instruction through a provided shared library and return the result.

    Args:
        - library (ctypes.CDLL): Shared library to process instructions.
        - instruction_context (pb.InstrContext): Instruction context.

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
    in_data = instruction_context.SerializeToString()
    in_ptr = (ctypes.c_uint8 * len(in_data))(*in_data)
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(1024 * 1024)  # Assume output size, adjust if necessary
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

    # Encode the bytes and return the object
    encode_output(output_object)
    return output_object


def raising_starmap(f, f_args, f_kwargs):
    assert f_args is None or f_kwargs is None or len(f_args) == len(f_kwargs)
    if f_args is None:
        f_args = repeat(tuple())
    elif f_kwargs is None:
        f_kwargs = repeat({})

    pool = Pool()

    def reraise(e):
        pool.terminate()
        raise e

    arg_and_kwargs = list(zip(f_args, f_kwargs))
    promises = [ pool.apply_async(f, args, kwargs, error_callback=reraise) for args, kwargs in arg_and_kwargs ]

    pool.close()
    print(pool._state)
    pool.join()


    if "TERMINATE" == pool._state:
        raise Exception(f"Error in raising starmap call to {f.__name__}")

    print(f"{len(promises)}/{len(arg_and_kwargs)} {f.__name__} calls succeeded.")
    return [ promise.get() for promise in promises ]
