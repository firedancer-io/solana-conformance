import fd58
from test_suite.context.codec_utils import encode_hex_compact, decode_hex_compact
import test_suite.invoke_pb2 as invoke_pb
import test_suite.vm_pb2 as vm_pb
from test_suite.instr.codec_utils import encode_input as instr_encode_input
from test_suite.instr.codec_utils import decode_input as instr_decode_input


def encode_input(input: vm_pb.SyscallContext):
    instr_ctx = invoke_pb.InstrContext()
    instr_ctx.CopyFrom(input.instr_ctx)
    instr_encode_input(instr_ctx)
    input.instr_ctx.CopyFrom(instr_ctx)
    if input.vm_ctx:
        if input.vm_ctx.rodata:
            input.vm_ctx.rodata = encode_hex_compact(input.vm_ctx.rodata)
        if input.vm_ctx.call_whitelist:
            input.vm_ctx.call_whitelist = encode_hex_compact(
                input.vm_ctx.call_whitelist
            )
        if input.vm_ctx.return_data:
            if input.vm_ctx.return_data.program_id:
                input.vm_ctx.return_data.program_id = fd58.enc32(
                    input.vm_ctx.return_data.program_id
                )
            if input.vm_ctx.return_data.data:
                input.vm_ctx.return_data.data = encode_hex_compact(
                    input.vm_ctx.return_data.data
                )

    if input.syscall_invocation:
        if input.syscall_invocation.function_name:
            input.syscall_invocation.function_name = encode_hex_compact(
                input.syscall_invocation.function_name
            )
        if input.syscall_invocation.stack_prefix:
            input.syscall_invocation.stack_prefix = encode_hex_compact(
                input.syscall_invocation.stack_prefix
            )
        if input.syscall_invocation.heap_prefix:
            input.syscall_invocation.heap_prefix = encode_hex_compact(
                input.syscall_invocation.heap_prefix
            )


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

    for i in range(len(effects.input_data_regions)):
        effects.input_data_regions[i].content = encode_hex_compact(
            effects.input_data_regions[i].content
        )


def decode_input(input: vm_pb.SyscallContext):
    instr_ctx = invoke_pb.InstrContext()
    instr_ctx.CopyFrom(input.instr_ctx)
    instr_decode_input(instr_ctx)
    input.instr_ctx.CopyFrom(instr_ctx)
    if input.vm_ctx:
        if input.vm_ctx.rodata:
            input.vm_ctx.rodata = decode_hex_compact(input.vm_ctx.rodata)
        if input.vm_ctx.call_whitelist:
            input.vm_ctx.call_whitelist = decode_hex_compact(
                input.vm_ctx.call_whitelist
            )
        if input.vm_ctx.return_data:
            if input.vm_ctx.return_data.program_id:
                input.vm_ctx.return_data.program_id = fd58.dec32(
                    input.vm_ctx.return_data.program_id
                )
            if input.vm_ctx.return_data.data:
                input.vm_ctx.return_data.data = decode_hex_compact(
                    input.vm_ctx.return_data.data
                )

    # Decode the syscall_invocation fields if present
    if input.syscall_invocation:
        if input.syscall_invocation.function_name:
            input.syscall_invocation.function_name = decode_hex_compact(
                input.syscall_invocation.function_name
            )
        if input.syscall_invocation.stack_prefix:
            input.syscall_invocation.stack_prefix = decode_hex_compact(
                input.syscall_invocation.stack_prefix
            )
        if input.syscall_invocation.heap_prefix:
            input.syscall_invocation.heap_prefix = decode_hex_compact(
                input.syscall_invocation.heap_prefix
            )
