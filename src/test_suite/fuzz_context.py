from test_suite.fuzz_interface import HarnessCtx

import test_suite.protos.txn_pb2 as txn_pb
import test_suite.txn.codec_utils as txn_codec
import test_suite.txn.prune_utils as txn_prune
import test_suite.txn.diff_utils as txn_diff
import test_suite.txn.transform_utils as txn_transform

import test_suite.protos.invoke_pb2 as invoke_pb
import test_suite.protos.elf_pb2 as elf_pb
import test_suite.protos.vm_pb2 as vm_pb
import test_suite.protos.block_pb2 as block_pb
import test_suite.protos.pack_pb2 as pack_pb
import test_suite.protos.type_pb2 as type_pb

import test_suite.block.codec_utils as block_codec

import test_suite.instr.codec_utils as instr_codec
import test_suite.instr.prune_utils as instr_prune
import test_suite.instr.transform_utils as instr_transform
import test_suite.instr.diff_utils as instr_diff

import test_suite.syscall.codec_utils as syscall_codec
import test_suite.syscall.transform_utils as syscall_transform

import test_suite.elf_loader.codec_utils as elf_codec

import test_suite.type.diff_utils as type_diff

ElfLoaderHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_elf_loader_v1",
    fixture_desc=elf_pb.ELFLoaderFixture.DESCRIPTOR,
    context_extension=".elfctx",
    context_human_encode_fn=elf_codec.encode_input,
    context_human_decode_fn=elf_codec.decode_input,
    effects_human_encode_fn=elf_codec.encode_output,
)

InstrHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_instr_execute_v1",
    fixture_desc=invoke_pb.InstrFixture.DESCRIPTOR,
    context_extension=".instrctx",
    # prune_effects_fn=instr_prune.prune_execution_result,
    context_human_encode_fn=instr_codec.encode_input,
    context_human_decode_fn=instr_codec.decode_input,
    effects_human_encode_fn=instr_codec.encode_output,
    consensus_diff_effect_fn=instr_diff.consensus_instr_diff_effects,
    core_bpf_diff_effect_fn=instr_diff.core_bpf_instr_diff_effects,
    ignore_compute_units_diff_effect_fn=instr_diff.ignore_compute_units_instr_diff_effects,
    regenerate_transformation_fn=instr_transform.transform_fixture,
)

SyscallHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_syscall_execute_v1",
    fixture_desc=vm_pb.SyscallFixture.DESCRIPTOR,
    context_extension=".syscallctx",
    context_human_encode_fn=syscall_codec.encode_input,
    effects_human_encode_fn=syscall_codec.encode_output,
    context_human_decode_fn=syscall_codec.decode_input,
    regenerate_transformation_fn=syscall_transform.transform_fixture,
)

VmInterpHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_interp_v1",
    fixture_desc=vm_pb.SyscallFixture.DESCRIPTOR,
    context_extension=".vmctx",
    context_human_encode_fn=syscall_codec.encode_input,
    effects_human_encode_fn=syscall_codec.encode_output,
    context_human_decode_fn=syscall_codec.decode_input,
    regenerate_transformation_fn=syscall_transform.transform_fixture,
)

VmValidateHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_vm_validate_v1",
    fixture_desc=vm_pb.ValidateVmFixture.DESCRIPTOR,
    context_extension=".vmvalidatectx",
)

TxnHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_txn_execute_v1",
    fixture_desc=txn_pb.TxnFixture.DESCRIPTOR,
    context_extension=".txnctx",
    # prune_effects_fn=txn_prune.prune_execution_result,
    context_human_encode_fn=txn_codec.encode_input,
    context_human_decode_fn=txn_codec.decode_input,
    effects_human_encode_fn=txn_codec.encode_output,
    regenerate_transformation_fn=txn_transform.transform_fixture,
    consensus_diff_effect_fn=txn_diff.consensus_txn_diff_effects,
)

PackComputeBudgetHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_pack_compute_budget_v1",
    fixture_desc=pack_pb.PackComputeBudgetFixture.DESCRIPTOR,
    context_extension=".packctx",
)

BlockHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_block_execute_v1",
    fixture_desc=block_pb.BlockFixture.DESCRIPTOR,
    context_extension=".blockctx",
    context_human_encode_fn=block_codec.encode_input,
    context_human_decode_fn=block_codec.decode_input,
    effects_human_encode_fn=block_codec.encode_output,
    # TODO: Fill in other fields...
)

TypeHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_type_execute_v1",
    fixture_desc=type_pb.TypeFixture.DESCRIPTOR,
    context_extension=".typectx",
    diff_effect_fn=type_diff.diff_type_effects,
)

ENTRYPOINT_HARNESS_MAP = {
    obj.fuzz_fn_name: obj for obj in globals().values() if isinstance(obj, HarnessCtx)
}
HARNESS_MAP = {
    name: obj for name, obj in globals().items() if isinstance(obj, HarnessCtx)
}

# Fixture extension (used by all harness types)
FIXTURE_EXTENSION = ".fix"

# ============================================================================
# FlatBuffers Support
# ============================================================================

# FlatBuffers is only supported for ELFLoaderHarness (schema exists in protosol)
# When adding FlatBuffers support for other harnesses, add them to FLATBUFFERS_HARNESSES below

# Add harnesses here when their FlatBuffers schemas are added to protosol
FLATBUFFERS_HARNESSES = {
    "ElfLoaderHarness",
}


def entrypoint_to_v2(entrypoint: str) -> str:
    """Convert a v1 entrypoint to v2 (for FlatBuffers output).

    Convention: _v1 suffix = Protobuf, _v2 suffix = FlatBuffers
    """
    if entrypoint and entrypoint.endswith("_v1"):
        return entrypoint[:-1] + "2"
    return entrypoint


def entrypoint_to_v1(entrypoint: str) -> str:
    """Convert a v2 entrypoint to v1 (for Protobuf output).

    Convention: _v1 suffix = Protobuf, _v2 suffix = FlatBuffers
    """
    if entrypoint and entrypoint.endswith("_v2"):
        return entrypoint[:-1] + "1"
    return entrypoint


# Cached set of entrypoints that support FlatBuffers (computed once at module load)
_FLATBUFFERS_ENTRYPOINTS: set[str] = None


def _get_flatbuffers_entrypoints() -> set[str]:
    """Get the set of entrypoints that support FlatBuffers (cached)."""
    global _FLATBUFFERS_ENTRYPOINTS
    if _FLATBUFFERS_ENTRYPOINTS is None:
        _FLATBUFFERS_ENTRYPOINTS = {
            HARNESS_MAP[h].fuzz_fn_name
            for h in FLATBUFFERS_HARNESSES
            if h in HARNESS_MAP
        }
    return _FLATBUFFERS_ENTRYPOINTS


def is_flatbuffers_supported(entrypoint: str) -> bool:
    """Check if an entrypoint supports FlatBuffers format.

    Currently only ELFLoaderFixture has FlatBuffers schema in protosol.
    To add support for new fixture types, add the harness name to FLATBUFFERS_HARNESSES.
    """
    if not entrypoint:
        return False
    # Normalize to v1 for lookup (handles both v1 and v2 inputs)
    normalized = entrypoint_to_v1(entrypoint)
    return normalized in _get_flatbuffers_entrypoints()


def get_harness_for_entrypoint(entrypoint: str) -> HarnessCtx:
    """
    Safely look up a harness by entrypoint, handling v1/v2 normalization.

    This handles:
    - v1 entrypoints (e.g., sol_compat_elf_loader_v1)
    - v2 entrypoints (e.g., sol_compat_elf_loader_v2) - normalized to v1
    - Unknown entrypoints - raises KeyError with helpful message

    Args:
        entrypoint: The function entrypoint name

    Returns:
        HarnessCtx for the entrypoint

    Raises:
        KeyError: If entrypoint is unknown (after normalization)
    """
    if not entrypoint:
        raise KeyError("Entrypoint is empty or None")

    # First try direct lookup
    if entrypoint in ENTRYPOINT_HARNESS_MAP:
        return ENTRYPOINT_HARNESS_MAP[entrypoint]

    # Try normalizing v2 -> v1
    normalized = entrypoint_to_v1(entrypoint)
    if normalized in ENTRYPOINT_HARNESS_MAP:
        return ENTRYPOINT_HARNESS_MAP[normalized]

    # Unknown entrypoint - provide helpful error message
    valid_entrypoints = sorted(ENTRYPOINT_HARNESS_MAP.keys())
    raise KeyError(
        f"Unknown entrypoint: '{entrypoint}'. "
        f"Valid entrypoints: {', '.join(valid_entrypoints)}"
    )


# All supported file extensions for create-fixtures and other commands
def get_all_supported_extensions() -> list[str]:
    extensions = [FIXTURE_EXTENSION]
    extensions.extend(harness.context_extension for harness in HARNESS_MAP.values())
    return list(set(extensions))


def _validate_harness_extensions():
    missing_extensions = []
    for name, harness in HARNESS_MAP.items():
        if not hasattr(harness, "context_extension") or not harness.context_extension:
            missing_extensions.append(name)

    if missing_extensions:
        raise ValueError(
            f"Missing context_extension for harness types: {', '.join(missing_extensions)}. "
            f"Please add context_extension parameter to: {missing_extensions}"
        )


# Run validation at module import time, all harnesses must have context extensions set
_validate_harness_extensions()
