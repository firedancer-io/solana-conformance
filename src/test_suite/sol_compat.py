import ctypes
from ctypes import c_uint64, c_int, POINTER, Structure
from dataclasses import dataclass, field
import os
import test_suite.globals as globals
from test_suite.constants import OUTPUT_BUFFER_SIZE


def initialize_process_output_buffers(randomize_output_buffer=False):
    """
    Initialize shared memory and pointers for output buffers for each process.

    Args:
        - randomize_output_buffer (bool): Whether to randomize output buffer.
    """
    globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)()

    if randomize_output_buffer:
        output_buffer_random_bytes = os.urandom(OUTPUT_BUFFER_SIZE)
        globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)(
            *output_buffer_random_bytes
        )


def exec_sol_compat_call(
    library: ctypes.CDLL,
    sol_compat_fn_name: str,
    input: str,
) -> bytearray | None:
    """
    Perform a sol_compat_ fuzz FFI call through a provided shared library
    and return the result.

    Args:
        - library (ctypes.CDLL): Shared library to process instructions.
        - input (str): bytes-like object to pass as input to the function.
                    Typically a serialized Context protobuf message.

    Returns:
        - bytearray | None: Result of function execution.
    """
    sol_compat_fn = getattr(library, sol_compat_fn_name)

    # Define argument and return types
    sol_compat_fn.argtypes = [
        POINTER(ctypes.c_uint8),  # out_ptr
        POINTER(c_uint64),  # out_psz
        POINTER(ctypes.c_uint8),  # in_ptr
        c_uint64,  # in_sz
    ]
    sol_compat_fn.restype = c_int

    # Prepare input data and output buffers
    in_data = input
    in_ptr = (ctypes.c_uint8 * len(in_data))(
        *in_data
    )  # create c_uint8 array from input data
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(OUTPUT_BUFFER_SIZE)

    # Call the function
    result = sol_compat_fn(
        globals.output_buffer_pointer, ctypes.byref(out_sz), in_ptr, in_sz
    )

    # Result == 0 means execution failed
    if result == 0:
        return None

    # Process the output
    output_data = bytearray(globals.output_buffer_pointer[: out_sz.value])

    return output_data


@dataclass
class FeaturePool:
    supported: list[int] = field(default_factory=list)
    hardcoded: list[int] = field(default_factory=list)


class sol_compat_features_t(Structure):
    _fields_ = [
        ("struct_size", c_uint64),
        ("hardcoded_features", POINTER(c_uint64)),
        ("hardcoded_feature_cnt", c_uint64),
        ("supported_features", POINTER(c_uint64)),
        ("supported_feature_cnt", c_uint64),
    ]


def get_feature_pool(library: ctypes.CDLL) -> FeaturePool:
    library.sol_compat_get_features_v1.argtypes = None
    library.sol_compat_get_features_v1.restype = POINTER(sol_compat_features_t)

    result = library.sol_compat_get_features_v1().contents
    if result.struct_size < 40:
        raise ValueError("sol_compat_get_features_v1 not supported")

    supported = [
        result.supported_features[i] for i in range(result.supported_feature_cnt)
    ]
    hardcoded = [
        result.hardcoded_features[i] for i in range(result.hardcoded_feature_cnt)
    ]
    return FeaturePool(supported, hardcoded)
