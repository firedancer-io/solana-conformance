import fd58
import test_suite.block_pb2 as block_pb
from test_suite.context.codec_utils import decode_acct_state, encode_acct_state
from test_suite.txn.codec_utils import decode_sanitized_tx, encode_sanitized_tx


def decode_input(context: block_pb.BlockContext):
    """
    Decode BlockContext fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.

    Args:
        - context (block_pb.BlockContext): Instruction context (will be modified).
    """
    if context.program_id:
        context.program_id = fd58.dec32(context.program_id)

    for i in range(len(context.microblocks)):
        for j in range(len(context.microblocks[i].txns)):
            decode_sanitized_tx(context.microblocks[i].txns[j])

    for i in range(len(context.acct_states)):
        decode_acct_state(context.acct_states[i])

    # POH hash
    context.slot_ctx.poh = fd58.dec32(context.slot_ctx.poh)

    # Parent bank hash
    context.slot_ctx.parent_bank_hash = fd58.dec32(context.slot_ctx.parent_bank_hash)

    # New stake accounts
    for i in range(len(context.epoch_ctx.new_stake_accounts)):
        context.epoch_ctx.new_stake_accounts[i] = fd58.dec32(
            context.epoch_ctx.new_stake_accounts[i]
        )

    # Stake accounts
    for i in range(len(context.epoch_ctx.stake_accounts)):
        context.epoch_ctx.stake_accounts[i].stake_account_pubkey = fd58.dec32(
            context.epoch_ctx.stake_accounts[i].stake_account_pubkey
        )
        context.epoch_ctx.stake_accounts[i].voter_pubkey = fd58.dec32(
            context.epoch_ctx.stake_accounts[i].voter_pubkey
        )

    # New vote accounts
    for i in range(len(context.epoch_ctx.new_vote_accounts)):
        context.epoch_ctx.new_vote_accounts[i] = fd58.dec32(
            context.epoch_ctx.new_vote_accounts[i]
        )

    # Vote accounts
    for i in range(len(context.epoch_ctx.vote_accounts_t)):
        decode_acct_state(context.epoch_ctx.vote_accounts_t[i].vote_account)

    # T-1 Vote accounts
    for i in range(len(context.epoch_ctx.vote_accounts_t_1)):
        decode_acct_state(context.epoch_ctx.vote_accounts_t_1[i].vote_account)

    # T-2 Vote accounts
    for i in range(len(context.epoch_ctx.vote_accounts_t_2)):
        decode_acct_state(context.epoch_ctx.vote_accounts_t_2[i].vote_account)

    # Blockhash queue
    for i in range(len(context.blockhash_queue)):
        context.blockhash_queue[i] = fd58.dec32(context.blockhash_queue[i])


def encode_input(context: block_pb.BlockContext):
    """
    Encode BlockContext fields in-place into binary, digestable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - context (block_pb.BlockContext): Instruction context (will be modified).
    """
    for i in range(len(context.microblocks)):
        for j in range(len(context.microblocks[i].txns)):
            encode_sanitized_tx(context.microblocks[i].txns[j])

    for i in range(len(context.acct_states)):
        encode_acct_state(context.acct_states[i])

    # POH hash
    context.slot_ctx.poh = fd58.enc32(context.slot_ctx.poh)

    # Parent bank hash
    context.slot_ctx.parent_bank_hash = fd58.enc32(context.slot_ctx.parent_bank_hash)

    # New stake accounts
    for i in range(len(context.epoch_ctx.new_stake_accounts)):
        context.epoch_ctx.new_stake_accounts[i] = fd58.enc32(
            context.epoch_ctx.new_stake_accounts[i]
        )

    # Stake accounts
    for i in range(len(context.epoch_ctx.stake_accounts)):
        context.epoch_ctx.stake_accounts[i].stake_account_pubkey = fd58.enc32(
            context.epoch_ctx.stake_accounts[i].stake_account_pubkey
        )
        context.epoch_ctx.stake_accounts[i].voter_pubkey = fd58.enc32(
            context.epoch_ctx.stake_accounts[i].voter_pubkey
        )

    # New vote accounts
    for i in range(len(context.epoch_ctx.new_vote_accounts)):
        context.epoch_ctx.new_vote_accounts[i] = fd58.enc32(
            context.epoch_ctx.new_vote_accounts[i]
        )

    # Vote accounts
    for i in range(len(context.epoch_ctx.vote_accounts_t)):
        encode_acct_state(context.epoch_ctx.vote_accounts_t[i].vote_account)

    # T-1 Vote accounts
    for i in range(len(context.epoch_ctx.vote_accounts_t_1)):
        encode_acct_state(context.epoch_ctx.vote_accounts_t_1[i].vote_account)

    # T-2 Vote accounts
    for i in range(len(context.epoch_ctx.vote_accounts_t_2)):
        encode_acct_state(context.epoch_ctx.vote_accounts_t_2[i].vote_account)

    # Blockhash queue
    for i in range(len(context.blockhash_queue)):
        context.blockhash_queue[i] = fd58.enc32(context.blockhash_queue[i])


def encode_output(effects: block_pb.BlockEffects):
    """
    Encode BlockEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - effects (block_pb.BlockEffects): Instruction effects (will be modified).
    """
    for i in range(len(effects.acct_states)):
        encode_acct_state(effects.acct_states[i])

    effects.bank_hash = fd58.enc32(effects.bank_hash)
    effects.lt_hash = fd58.enc32(effects.lt_hash)
    effects.account_delta_hash = fd58.enc32(effects.account_delta_hash)
