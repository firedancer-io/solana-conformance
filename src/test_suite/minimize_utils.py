from pathlib import Path
import test_suite.invoke_pb2 as pb
import test_suite.globals as globals
from test_suite.multiprocessing_utils import (
    generate_test_case,
    process_instruction,
)


def minimize_single_test_case(test_file: Path) -> int:
    """
    Minimize a single test case by pruning any additional accounts / features that do not
    affect output.

    Args:
        test_file (Path): The test file to minimize

    Returns:
        int: 0 on failure, 1 on success
    """
    _, serialized_instruction_context = generate_test_case(test_file)

    # Skip if input is invalid
    if serialized_instruction_context is None:
        return 0

    lib = globals.target_libraries[globals.solana_shared_library]

    # Get a base output result (could be None)
    baseline_instruction_effects = process_instruction(
        lib, serialized_instruction_context
    )

    # Skip if input could not be processed
    if baseline_instruction_effects is None:
        return 0

    # Serialize the instruction effects
    serialized_baseline_instruction_effects = (
        baseline_instruction_effects.SerializeToString(deterministic=True)
    )

    # Deserialize the instruction context
    instruction_context = pb.InstrContext()
    instruction_context.ParseFromString(serialized_instruction_context)

    # Incrementally remove features and test the output
    feature_count = len(instruction_context.epoch_context.features.features)
    feature_idx = feature_count - 1
    while feature_idx >= 0:
        removed_feature = instruction_context.epoch_context.features.features[
            feature_idx
        ]
        del instruction_context.epoch_context.features.features[feature_idx]
        test_instruction_effects = process_instruction(
            lib, instruction_context.SerializeToString(deterministic=True)
        )
        serialized_test_instruction_effects = (
            test_instruction_effects.SerializeToString(deterministic=True)
        )
        if (
            serialized_baseline_instruction_effects
            != serialized_test_instruction_effects
        ):
            instruction_context.epoch_context.features.features.extend(
                [removed_feature]
            )
        feature_idx -= 1

    features = (
        list(instruction_context.epoch_context.features.features)
        + globals.feature_pool.hardcoded
    )
    del instruction_context.epoch_context.features.features[:]
    instruction_context.epoch_context.features.features.extend(sorted(set(features)))

    with open(globals.output_dir / test_file.name, "wb") as f:
        f.write(instruction_context.SerializeToString(deterministic=True))
    return 1
