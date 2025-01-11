from test_suite.fuzz_interface import HarnessCtx

import test_suite.txn_pb2 as txn_pb
import test_suite.txn.codec_utils as txn_codec
import test_suite.txn.prune_utils as txn_prune
import test_suite.txn.diff_utils as txn_diff
import test_suite.txn.transform_utils as txn_transform

import test_suite.invoke_pb2 as invoke_pb
import test_suite.instr.codec_utils as instr_codec
import test_suite.instr.prune_utils as instr_prune
import test_suite.instr.transform_utils as instr_transform
import test_suite.instr.diff_utils as instr_diff

import test_suite.elf_pb2 as elf_pb

import test_suite.vm_pb2 as vm_pb

import test_suite.syscall.codec_utils as syscall_codec


ElfLoaderHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_elf_loader_v1",
    fixture_desc=elf_pb.ELFLoaderFixture.DESCRIPTOR,
)

InstrHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_instr_execute_v1",
    fixture_desc=invoke_pb.InstrFixture.DESCRIPTOR,
    prune_effects_fn=instr_prune.prune_execution_result,
    context_human_encode_fn=instr_codec.encode_input,
    context_human_decode_fn=instr_codec.decode_input,
    effects_human_encode_fn=instr_codec.encode_output,
    consensus_diff_effect_fn=instr_diff.consensus_instr_diff_effects,
    core_bpf_diff_effect_fn=instr_diff.core_bpf_instr_diff_effects,
    regenerate_transformation_fn=instr_transform.transform_fixture,
)

SyscallHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_syscall_execute_v1",
    fixture_desc=vm_pb.SyscallFixture.DESCRIPTOR,
    context_human_encode_fn=syscall_codec.encode_input,
    effects_human_encode_fn=syscall_codec.encode_output,
    context_human_decode_fn=syscall_codec.decode_input,
)

CpiHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_cpi_syscall_v1",
    fixture_desc=vm_pb.SyscallFixture.DESCRIPTOR,
    context_human_encode_fn=syscall_codec.encode_input,
    effects_human_encode_fn=syscall_codec.encode_output,
    context_human_decode_fn=syscall_codec.decode_input,
)

VmInterpHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_interp_v1",
    fixture_desc=vm_pb.SyscallFixture.DESCRIPTOR,
    context_human_encode_fn=syscall_codec.encode_input,
    effects_human_encode_fn=syscall_codec.encode_output,
    context_human_decode_fn=syscall_codec.decode_input,
)

VmValidateHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_validate_v1",
    fixture_desc=vm_pb.ValidateVmFixture.DESCRIPTOR,
)

TxnHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_txn_execute_v1",
    fixture_desc=txn_pb.TxnFixture.DESCRIPTOR,
    # prune_effects_fn=txn_prune.prune_execution_result,
    context_human_encode_fn=txn_codec.encode_input,
    context_human_decode_fn=txn_codec.decode_input,
    effects_human_encode_fn=txn_codec.encode_output,
    regenerate_transformation_fn=txn_transform.transform_fixture,
    consensus_diff_effect_fn=txn_diff.consensus_txn_diff_effects,
)

ENTRYPOINT_HARNESS_MAP = {
    obj.fuzz_fn_name: obj
    for name, obj in globals().items()
    if isinstance(obj, HarnessCtx)
}
HARNESS_MAP = {
    name: obj for name, obj in globals().items() if isinstance(obj, HarnessCtx)
}
