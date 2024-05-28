import base64
import test_suite.invoke_pb2 as pb


def encode_output(effects: pb.SyscallEffects):
    """
    Encode SyscallEffects fields in-place into human-readable format.
    Heap is hex, Stack is temp hidden.

    Args:
        - effects (pb.SyscallEffects): Syscall effects (will be modified).
    """
    effects.heap = base64.b16encode(effects.heap)
    effects.stack = b""
