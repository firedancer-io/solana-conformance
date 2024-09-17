import fd58
import test_suite.exec_v2_pb2 as exec_v2_pb


def decode_input(exec_context: exec_v2_pb.ExecEnv):
    if exec_context.harness_type != exec_v2_pb.HarnessType.INSTR:
        return

    # Account states
    for account in exec_context.acct_states:
        account.address = fd58.dec32(account.address)
        account.owner = fd58.dec32(account.owner)

    # Features
    for feature in exec_context.features:
        feature.feature_id = fd58.dec32(feature.feature_id)

    # Account keys
    txn_env = exec_context.slots[0].txns[0]
    for i in range(len(txn_env.account_keys)):
        txn_env.account_keys[i] = fd58.dec32(txn_env.account_keys[i])


def encode_input(exec_context: exec_v2_pb.ExecEnv):
    if exec_context.harness_type != exec_v2_pb.HarnessType.INSTR:
        return

    # Account states
    for account in exec_context.acct_states:
        account.address = fd58.enc32(account.address)
        account.owner = fd58.enc32(account.owner)

    # Features
    for feature in exec_context.features:
        feature.feature_id = fd58.enc32(feature.feature_id)

    # Account keys
    txn_env = exec_context.slots[0].txns[0]
    for i in range(len(txn_env.account_keys)):
        txn_env.account_keys[i] = fd58.enc32(txn_env.account_keys[i])


def encode_output(exec_effects: exec_v2_pb.ExecEffects):
    if exec_effects.harness_type != exec_v2_pb.HarnessType.INSTR:
        return

    # Account states
    for account in exec_effects.acct_states:
        account.address = fd58.enc32(account.address)
        account.owner = fd58.enc32(account.owner)
