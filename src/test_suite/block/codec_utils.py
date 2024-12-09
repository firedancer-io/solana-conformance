import fd58
import test_suite.block_pb2 as block_pb


def decode_input(context: block_pb.BlockContext):
    """
    Decode BlockContext fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.

    Args:
        - context (block_pb.BlockContext): Instruction context (will be modified).
    """
    if context.program_id:
        context.program_id = fd58.dec32(context.program_id)

    for i in range(len(context.accounts)):
        if context.accounts[i].address:
            context.accounts[i].address = fd58.dec32(context.accounts[i].address)
        if context.accounts[i].owner:
            context.accounts[i].owner = fd58.dec32(context.accounts[i].owner)


def encode_input(context: block_pb.BlockContext):
    """
    Encode BlockContext fields in-place into binary, digestable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - context (block_pb.BlockContext): Instruction context (will be modified).
    """
    if context.program_id:
        context.program_id = fd58.enc32(context.program_id)

    for i in range(len(context.accounts)):
        if context.accounts[i].address:
            context.accounts[i].address = fd58.enc32(context.accounts[i].address)
        if context.accounts[i].owner:
            context.accounts[i].owner = fd58.enc32(context.accounts[i].owner)


def encode_output(effects: block_pb.BlockEffects):
    """
    Encode BlockEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - effects (block_pb.BlockEffects): Instruction effects (will be modified).
    """
    for i in range(len(effects.acct_states)):
        if effects.acct_states[i].address:
            effects.acct_states[i].address = fd58.enc32(effects.acct_states[i].address)
        if effects.acct_states[i].owner:
            effects.acct_states[i].owner = fd58.enc32(effects.acct_states[i].owner)

    # TODO: lt_hash, account delta hash
