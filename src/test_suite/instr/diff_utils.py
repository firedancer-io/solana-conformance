from enum import Enum
import test_suite.invoke_pb2 as invoke_pb


class DiffMode(Enum):
    STANDARD = 0
    CONSENSUS = 1
    CORE_BPF = 2

    def apply_diff(self, a: invoke_pb.InstrEffects, b: invoke_pb.InstrEffects):
        """Applies the specified diff effects.
        - STANDARD: No diff effects.
        - CONSENSUS: Consensus-only diff effects.
        - CORE_BPF: Core BPF diff effects for testing a BPF program against a builtin.
        """
        if self == DiffMode.CONSENSUS:
            return consensus_instr_diff_effects(a, b)
        if self == DiffMode.CORE_BPF:
            return core_bpf_instr_diff_effects(a, b)


def consensus_instr_diff_effects(a: invoke_pb.InstrEffects, b: invoke_pb.InstrEffects):
    a_san = invoke_pb.InstrEffects()
    a_san.CopyFrom(a)
    b_san = invoke_pb.InstrEffects()
    b_san.CopyFrom(b)

    # Normalize error codes and cus
    a_san.result = 0
    a_san.custom_err = 0
    a_san.cu_avail = 0

    b_san.result = 0
    b_san.custom_err = 0
    b_san.cu_avail = 0

    return a_san == b_san


def core_bpf_instr_diff_effects(a: invoke_pb.InstrEffects, b: invoke_pb.InstrEffects):
    a_san = invoke_pb.InstrEffects()
    a_san.CopyFrom(a)
    b_san = invoke_pb.InstrEffects()
    b_san.CopyFrom(b)

    # If the result is an error (not 0), don't return modified accounts.
    if a_san.result != 0:
        while len(a_san.modified_accounts) > 0:
            a_san.modified_accounts.pop()
    if b_san.result != 0:
        while len(b_san.modified_accounts) > 0:
            b_san.modified_accounts.pop()

    # Normalize error codes and cus
    a_san.result = 0
    a_san.custom_err = 0
    a_san.cu_avail = 0

    b_san.result = 0
    b_san.custom_err = 0
    b_san.cu_avail = 0

    return a_san == b_san
