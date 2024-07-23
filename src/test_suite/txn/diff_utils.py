import test_suite.txn_pb2 as txn_pb


def txn_diff_effects(a_san: txn_pb.TxnResult, b_san: txn_pb.TxnResult):
    for i in range(len(a_san.resulting_state.acct_states)):
        a_san.resulting_state.acct_states[i].rent_epoch = 0

    for i in range(len(b_san.resulting_state.acct_states)):
        b_san.resulting_state.acct_states[i].rent_epoch = 0

    if a_san.status and b_san.status:
        a_san.status = 1
        b_san.status = 1
        a_san.executed_units = 0
        b_san.executed_units = 0

    return a_san == b_san
