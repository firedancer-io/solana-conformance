import fd58
from test_suite.context.codec_utils import decode_acct_state, encode_acct_state
from test_suite.fuzz_interface import decode_hex_compact, encode_hex_compact
import test_suite.invoke_pb2 as invoke_pb


def decode_input(instruction_context: invoke_pb.InstrContext):
    """
    Decode InstrContext fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.

    Args:
        - instruction_context (invoke_pb.InstrContext): Instruction context (will be modified).
    """
    # Program ID
    if instruction_context.program_id:
        instruction_context.program_id = fd58.dec32(instruction_context.program_id)

    # Accounts
    for i in range(len(instruction_context.accounts)):
        decode_acct_state(instruction_context.accounts[i])

    # Data
    if instruction_context.data:
        instruction_context.data = decode_hex_compact(instruction_context.data)


def encode_input(instruction_context: invoke_pb.InstrContext):
    """
    Encode InstrContext fields in-place into binary, digestable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - instruction_context (invoke_pb.InstrContext): Instruction context (will be modified).
    """
    # Program ID
    if instruction_context.program_id:
        instruction_context.program_id = fd58.enc32(instruction_context.program_id)

    # Accounts
    for i in range(len(instruction_context.accounts)):
        encode_acct_state(instruction_context.accounts[i])

    # Data
    if instruction_context.data:
        instruction_context.data = encode_hex_compact(instruction_context.data)


def encode_output(instruction_effects: invoke_pb.InstrEffects):
    """
    Encode InstrEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - instruction_effects (invoke_pb.InstrEffects): Instruction effects (will be modified).
    """
    # Accounts
    for i in range(len(instruction_effects.modified_accounts)):
        encode_acct_state(instruction_effects.modified_accounts[i])

    # Return data
    if instruction_effects.return_data:
        instruction_effects.return_data = encode_hex_compact(
            instruction_effects.return_data
        )
