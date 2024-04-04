import test_suite.invoke_pb2 as pb


def is_valid(instruction_context: pb.InstrContext) -> bool:
    """
    Checks whether an instruction context message is valid.

    Args:
        - instruction_context (pb.InstrContext): Instruction context message.
    Returns:
        - bool: True if valid, False otherwise.
    """
    for account in instruction_context.accounts:
        if not account.address or len(account.address) != 32:
            return False

    return instruction_context.data and instruction_context.instr_accounts
