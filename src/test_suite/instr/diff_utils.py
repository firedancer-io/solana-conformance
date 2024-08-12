import test_suite.invoke_pb2 as invoke_pb


def consensus_instr_diff_effects(a: invoke_pb.InstrEffects, b: invoke_pb.InstrEffects):
    a_san = invoke_pb.InstrEffects()
    a_san.CopyFrom(a)
    b_san = invoke_pb.InstrEffects()
    b_san.CopyFrom(b)

    # Normalize error codes
    a_san.result = 0
    a_san.custom_err = 0

    b_san.result = 0
    b_san.custom_err = 0

    return a_san == b_san
