import test_suite.globals as globals
import test_suite.exec_v2_pb2 as exec_v2_pb
from test_suite.validation_utils import check_account_unchanged


def prune_execution_result(
    serialized_context: str | None,
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
    if serialized_context is None:
        return None

    context = globals.harness_ctx.context_type()
    context.ParseFromString(serialized_context)

    targets_to_serialized_pruned_instruction_effects = {}
    for (
        target,
        serialized_instruction_effects,
    ) in targets_to_serialized_effects.items():
        if serialized_instruction_effects is None:
            targets_to_serialized_pruned_instruction_effects[target] = None
            continue

        exec_effects = exec_v2_pb.ExecEffects()
        exec_effects.ParseFromString(serialized_instruction_effects)

        # O(n^2) because not performance sensitive
        new_modified_accounts = []
        for modified_account in exec_effects.acct_states:
            account_unchanged = False
            for beginning_account_state in context.acct_states:
                account_unchanged |= check_account_unchanged(
                    modified_account, beginning_account_state
                )

            if not account_unchanged:
                new_modified_accounts.append(modified_account)

        # Assign new modified accounts
        del exec_effects.acct_states[:]
        exec_effects.acct_states.extend(new_modified_accounts)
        targets_to_serialized_pruned_instruction_effects[target] = (
            exec_effects.SerializeToString(deterministic=True)
        )

    return targets_to_serialized_pruned_instruction_effects
