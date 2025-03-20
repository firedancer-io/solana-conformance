import fd58
from test_suite.context.codec_utils import decode_acct_state, encode_acct_state
import test_suite.invoke_pb2 as invoke_pb


def decode_input(instruction_context: invoke_pb.InstrContext):
    """
    Decode InstrContext fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.

    Args:
        - instruction_context (invoke_pb.InstrContext): Instruction context (will be modified).
    """
    if instruction_context.program_id:
        instruction_context.program_id = fd58.dec32(instruction_context.program_id)

    for i in range(len(instruction_context.accounts)):
        decode_acct_state(instruction_context.accounts[i])


def encode_input(instruction_context: invoke_pb.InstrContext):
    """
    Encode InstrContext fields in-place into binary, digestable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - instruction_context (invoke_pb.InstrContext): Instruction context (will be modified).
    """
    if instruction_context.program_id:
        instruction_context.program_id = fd58.enc32(instruction_context.program_id)

    for i in range(len(instruction_context.accounts)):
        encode_acct_state(instruction_context.accounts[i])


def encode_output(instruction_effects: invoke_pb.InstrEffects):
    """
    Encode InstrEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - instruction_effects (invoke_pb.InstrEffects): Instruction effects (will be modified).
    """
    for i in range(len(instruction_effects.modified_accounts)):
        encode_acct_state(instruction_effects.modified_accounts[i])
