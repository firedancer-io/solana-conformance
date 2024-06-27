import base64
import fd58
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
        if instruction_context.accounts[i].address:
            instruction_context.accounts[i].address = fd58.dec32(
                instruction_context.accounts[i].address
            )
        if instruction_context.accounts[i].data:
            instruction_context.accounts[i].data = base64.b64decode(
                instruction_context.accounts[i].data
            )
        if instruction_context.accounts[i].owner:
            instruction_context.accounts[i].owner = fd58.dec32(
                instruction_context.accounts[i].owner
            )

    if instruction_context.data:
        instruction_context.data = base64.b64decode(instruction_context.data)


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
        if instruction_context.accounts[i].address:
            instruction_context.accounts[i].address = fd58.enc32(
                instruction_context.accounts[i].address
            )
        if instruction_context.accounts[i].data:
            instruction_context.accounts[i].data = base64.b64encode(
                instruction_context.accounts[i].data
            )
        if instruction_context.accounts[i].owner:
            instruction_context.accounts[i].owner = fd58.enc32(
                instruction_context.accounts[i].owner
            )

    if instruction_context.data:
        instruction_context.data = base64.b64encode(instruction_context.data)


def encode_output(instruction_effects: invoke_pb.InstrEffects):
    """
    Encode InstrEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - instruction_effects (invoke_pb.InstrEffects): Instruction effects (will be modified).
    """
    for i in range(len(instruction_effects.modified_accounts)):
        if instruction_effects.modified_accounts[i].address:
            instruction_effects.modified_accounts[i].address = fd58.enc32(
                instruction_effects.modified_accounts[i].address
            )
        if instruction_effects.modified_accounts[i].data:
            instruction_effects.modified_accounts[i].data = base64.b64encode(
                instruction_effects.modified_accounts[i].data
            )
        if instruction_effects.modified_accounts[i].owner:
            instruction_effects.modified_accounts[i].owner = fd58.enc32(
                instruction_effects.modified_accounts[i].owner
            )
