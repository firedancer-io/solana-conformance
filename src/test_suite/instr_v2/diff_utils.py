import test_suite.exec_v2_pb2 as exec_v2_pb


def consensus_instr_diff_effects(a: exec_v2_pb.ExecEffects, b: exec_v2_pb.ExecEffects):
    a_san = exec_v2_pb.ExecEffects()
    a_san.CopyFrom(a)
    b_san = exec_v2_pb.ExecEffects()
    b_san.CopyFrom(b)

    # Normalize error codes
    a_san.slot_effects[0].txn_effects[0].instr_effects[0].result = 0
    a_san.slot_effects[0].txn_effects[0].instr_effects[0].custom_err = 0

    b_san.slot_effects[0].txn_effects[0].instr_effects[0].result = 0
    b_san.slot_effects[0].txn_effects[0].instr_effects[0].custom_err = 0

    return a_san == b_san
