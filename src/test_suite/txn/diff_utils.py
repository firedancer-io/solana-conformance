import test_suite.txn_pb2 as txn_pb


def txn_diff_effects(a: txn_pb.TxnResult, b: txn_pb.TxnResult):
    a_san = txn_pb.TxnResult()
    a_san.CopyFrom(a)
    b_san = txn_pb.TxnResult()
    b_san.CopyFrom(b)

    # Don't compare rent epochs
    for i in range(len(a_san.resulting_state.acct_states)):
        a_san.resulting_state.acct_states[i].rent_epoch = 0

    for i in range(len(b_san.resulting_state.acct_states)):
        b_san.resulting_state.acct_states[i].rent_epoch = 0

    # Don't compare compute units if both txns were executed and fail
    if a_san.executed and b_san.executed and a_san.status and b_san.status:
        a_san.executed_units = 0
        b_san.executed_units = 0

    if a_san.status == 999:
        a_san.status = b_san.status
    if b_san.status == 999:
        b_san.status = a_san.status

    return a_san == b_san


def consensus_txn_diff_effects(a: txn_pb.TxnResult, b: txn_pb.TxnResult):
    a_san = txn_pb.TxnResult()
    a_san.CopyFrom(a)
    b_san = txn_pb.TxnResult()
    b_san.CopyFrom(b)

    # Don't compare rent epochs
    for i in range(len(a_san.resulting_state.acct_states)):
        a_san.resulting_state.acct_states[i].rent_epoch = 0

    for i in range(len(b_san.resulting_state.acct_states)):
        b_san.resulting_state.acct_states[i].rent_epoch = 0

    # Don't compare transaction statuses and compute units if both txns were executed and fail
    if a_san.executed and b_san.executed and a_san.status and b_san.status:
        a_san.executed_units = 0
        b_san.executed_units = 0

    # Don't compare error codes
    a_san.status = 0
    a_san.instruction_error = 0
    a_san.instruction_error_index = 0
    a_san.custom_error = 0

    b_san.status = 0
    b_san.instruction_error = 0
    b_san.instruction_error_index = 0
    b_san.custom_error = 0

    return a_san == b_san
