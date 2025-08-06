import test_suite.context_pb2 as context_pb
import fd58
from test_suite.fuzz_interface import encode_hex_compact, decode_hex_compact


def encode_acct_state(acct_state: context_pb.AcctState):
    # Pubkey
    if acct_state.address:
        acct_state.address = fd58.enc32(acct_state.address)

    # Owner
    if acct_state.owner:
        acct_state.owner = fd58.enc32(acct_state.owner)

    # Data
    if acct_state.data:
        acct_state.data = encode_hex_compact(acct_state.data)


def decode_acct_state(acct_state: context_pb.AcctState):
    # Pubkey
    if acct_state.address:
        acct_state.address = fd58.dec32(acct_state.address)

    # Owner
    if acct_state.owner:
        acct_state.owner = fd58.dec32(acct_state.owner)

    # Data
    if acct_state.data:
        acct_state.data = decode_hex_compact(acct_state.data)
