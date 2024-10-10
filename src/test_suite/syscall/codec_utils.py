import base64
import test_suite.vm_pb2 as vm_pb
from test_suite.fuzz_interface import encode_hex_compact


def encode_output(effects: vm_pb.SyscallEffects):
    """
    Encode SyscallEffects fields in-place into human-readable format.
    Heap is hex, Stack is temp hidden.

    Args:
        - effects (vm_pb.SyscallEffects): Syscall effects (will be modified).
    """
    effects.heap = encode_hex_compact(effects.heap)
    effects.stack = encode_hex_compact(effects.stack)
    effects.rodata = encode_hex_compact(effects.rodata)
