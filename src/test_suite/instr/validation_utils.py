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


def check_account_unchanged(acc1: pb.AcctState, acc2: pb.AcctState) -> bool:
    """
    Checks whether two account states are equal.

    Args:
        - acc1 (pb.AcctState): Account state message.
        - acc2 (pb.AcctState): Account state message.

    Returns:
        - bool: True if equal, False otherwise.
    """

    return (
        acc1.address == acc2.address
        and acc1.lamports == acc2.lamports
        and acc1.data == acc2.data
        and acc1.executable == acc2.executable
        and acc1.rent_epoch == acc2.rent_epoch
        and acc1.owner == acc2.owner
    )
