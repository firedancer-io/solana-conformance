from test_suite.fuzz_interface import ContextType
import test_suite.globals as globals
import test_suite.protos.invoke_pb2 as invoke_pb
import test_suite.protos.context_pb2 as context_pb
from test_suite.validation_utils import check_account_unchanged


def prune_execution_result(
    context: ContextType | None,
    targets_to_serialized_effects: dict[str, str | None],
) -> dict[str, str | None] | None:
    """
    Prune execution result to only include actually modified accounts.

    Args:
        - serialized_context (str | None): Serialized instruction context.
        - targets_to_serialized_effects (dict[str, str | None]): Dictionary of target library names and serialized instruction effects.

    Returns:
        - dict[str, str | None] | None: Serialized pruned instruction effects for each target.
    """
    targets_to_serialized_pruned_instruction_effects = {}
    for (
        target,
        serialized_instruction_effects,
    ) in targets_to_serialized_effects.items():
        if serialized_instruction_effects is None:
            targets_to_serialized_pruned_instruction_effects[target] = None
            continue

        instruction_effects = invoke_pb.InstrEffects()
        instruction_effects.ParseFromString(serialized_instruction_effects)

        # O(n^2) because not performance sensitive
        new_modified_accounts: list[context_pb.AcctState] = []
        for modified_account in instruction_effects.modified_accounts:
            account_unchanged = False
            for beginning_account_state in context.accounts:
                account_unchanged |= check_account_unchanged(
                    modified_account, beginning_account_state
                )

            if not account_unchanged:
                new_modified_accounts.append(modified_account)

        # Assign new modified accounts
        del instruction_effects.modified_accounts[:]
        instruction_effects.modified_accounts.extend(new_modified_accounts)
        targets_to_serialized_pruned_instruction_effects[target] = (
            instruction_effects.SerializeToString(deterministic=True)
        )

    return targets_to_serialized_pruned_instruction_effects
