import fd58
import test_suite.protos.block_pb2 as block_pb
from test_suite.context.codec_utils import decode_acct_state, encode_acct_state
from test_suite.txn.codec_utils import decode_sanitized_tx, encode_sanitized_tx


def _decode_prev_vote_account(pva):
    if pva.address:
        pva.address = fd58.dec32(pva.address)
    if pva.node_pubkey:
        pva.node_pubkey = fd58.dec32(pva.node_pubkey)


def _encode_prev_vote_account(pva):
    if pva.address:
        pva.address = fd58.enc32(pva.address)
    if pva.node_pubkey:
        pva.node_pubkey = fd58.enc32(pva.node_pubkey)


def decode_input(context: block_pb.BlockContext):
    """
    Decode BlockContext fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.

    Args:
        - context (block_pb.BlockContext): Instruction context (will be modified).
    """
    for i in range(len(context.txns)):
        decode_sanitized_tx(context.txns[i])

    for i in range(len(context.acct_states)):
        decode_acct_state(context.acct_states[i])

    # POH hash
    context.bank.poh = fd58.dec32(context.bank.poh)

    # Parent bank hash
    context.bank.parent_bank_hash = fd58.dec32(context.bank.parent_bank_hash)

    # T-1 Vote accounts
    for i in range(len(context.bank.vote_accounts_t_1)):
        _decode_prev_vote_account(context.bank.vote_accounts_t_1[i])

    # T-2 Vote accounts
    for i in range(len(context.bank.vote_accounts_t_2)):
        _decode_prev_vote_account(context.bank.vote_accounts_t_2[i])

    # Blockhash queue
    for i in range(len(context.bank.blockhash_queue)):
        context.bank.blockhash_queue[i].blockhash = fd58.dec32(
            context.bank.blockhash_queue[i].blockhash
        )


def encode_input(context: block_pb.BlockContext):
    """
    Encode BlockContext fields in-place into binary, digestable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - context (block_pb.BlockContext): Instruction context (will be modified).
    """
    for i in range(len(context.txns)):
        encode_sanitized_tx(context.txns[i])

    for i in range(len(context.acct_states)):
        encode_acct_state(context.acct_states[i])

    # POH hash
    context.bank.poh = fd58.enc32(context.bank.poh)

    # Parent bank hash
    context.bank.parent_bank_hash = fd58.enc32(context.bank.parent_bank_hash)

    # T-1 Vote accounts
    for i in range(len(context.bank.vote_accounts_t_1)):
        _encode_prev_vote_account(context.bank.vote_accounts_t_1[i])

    # T-2 Vote accounts
    for i in range(len(context.bank.vote_accounts_t_2)):
        _encode_prev_vote_account(context.bank.vote_accounts_t_2[i])

    # Blockhash queue
    for i in range(len(context.bank.blockhash_queue)):
        context.bank.blockhash_queue[i].blockhash = fd58.enc32(
            context.bank.blockhash_queue[i].blockhash
        )


def encode_output(effects: block_pb.BlockEffects):
    """
    Encode BlockEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - effects (block_pb.BlockEffects): Instruction effects (will be modified).
    """
    if effects.bank_hash:
        effects.bank_hash = fd58.enc32(effects.bank_hash)


def decode_output(effects: block_pb.BlockEffects):
    """
    Decode BlockEffects fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.
    """
    if effects.bank_hash:
        effects.bank_hash = fd58.dec32(effects.bank_hash)
