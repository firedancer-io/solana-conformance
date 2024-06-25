import base64
import test_suite.vm_pb2 as vm_pb


def encode_output(effects: vm_pb.SyscallEffects):
    """
    Encode SyscallEffects fields in-place into human-readable format.
    Heap is hex, Stack is temp hidden.

    Args:
        - effects (vm_pb.SyscallEffects): Syscall effects (will be modified).
    """
    effects.heap = base64.b16encode(effects.heap)
    effects.stack = b""
