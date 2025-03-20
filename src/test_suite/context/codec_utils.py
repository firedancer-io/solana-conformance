import test_suite.context_pb2 as context_pb
import fd58


def encode_acct_state(acct_state: context_pb.AcctState):
    # Pubkey
    if acct_state.address:
        acct_state.address = fd58.enc32(acct_state.address)

    # Owner
    if acct_state.owner:
        acct_state.owner = fd58.enc32(acct_state.owner)


def decode_acct_state(acct_state: context_pb.AcctState):
    # Pubkey
    if acct_state.address:
        acct_state.address = fd58.dec32(acct_state.address)

    # Owner
    if acct_state.owner:
        acct_state.owner = fd58.dec32(acct_state.owner)
