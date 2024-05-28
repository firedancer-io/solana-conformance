from test_suite.fuzz_interface import HarnessCtx
import test_suite.invoke_pb2 as pb
import test_suite.instr.codec_utils as instr_codec
import test_suite.syscall.codec_utils as syscall_codec


ElfHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_elf_loader_v1", fixture_desc=pb.ELFLoaderFixture.DESCRIPTOR
)

InstrHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_instr_execute_v1",
    fixture_desc=pb.InstrFixture.DESCRIPTOR,
    context_human_encode_fn=instr_codec.encode_input,
    context_human_decode_fn=instr_codec.decode_input,
    effects_human_encode_fn=instr_codec.encode_output,
)

SyscallHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_syscall_execute_v1",
    fixture_desc=pb.SyscallFixture.DESCRIPTOR,
    effects_human_encode_fn=syscall_codec.encode_output,
)
