from test_suite.sol_compat import (
    exec_sol_compat_call,
)
import test_suite.invoke_pb2 as pb
import ctypes


def process_elf_loader_ctx(
    lib: ctypes.CDLL, ctx_str: str
) -> pb.ELFLoaderEffects | None:
    """
    Process a serialized ELFLoaderCtx protobuf message using the
    sol_compat_elf_loader_v1 function.

    Assumes that the shared library has a function named sol_compat_elf_loader_v1.
    Assumes *_compat_init/fini functions are wrapped around this function.

    Args:
        - lib (ctypes.CDLL): Shared library to process instructions.
        - ctx (pb.ELFLoaderCtx): ELFLoaderCtx protobuf message to process.

    Returns:
        - pb.ELFLoaderEffects: ELFLoaderEffects protobuf message.
    """

    # Call sol_compat_elf_loader_v1
    out_data = exec_sol_compat_call(lib, "sol_compat_elf_loader_v1", ctx_str)
    if out_data is None:
        return None
    elf_loader_effects = pb.ELFLoaderEffects()
    elf_loader_effects.ParseFromString(out_data)
    return elf_loader_effects
