import test_suite.invoke_pb2 as pb


def is_valid(instruction_context: pb.InstrContext) -> bool:
    """
    Checks whether an instruction context message is valid.

    Args:
        - instruction_context (pb.InstrContext): Instruction context message.
    Returns:
        - bool: True if valid, False otherwise.
    """
    if len(instruction_context.program_id) != 32:
        return False

    for account in instruction_context.accounts:
        if not account.address or len(account.address) != 32:
            return False

    return True
