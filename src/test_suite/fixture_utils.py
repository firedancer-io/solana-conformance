from test_suite.multiprocessing_utils import prune_execution_result
import test_suite.globals as globals
import test_suite.invoke_pb2 as pb


def create_fixture(
    file_serialized_instruction_context: tuple[str, dict],
    file_serialized_instruction_effects: tuple[str, dict[str, str | None]],
) -> tuple[str, str | None]:
    """
    Create instruction fixture for an instruction context and effects.

    Args:
        - file_serialized_instruction_context (tuple[str, str]): Tuple of file stem and serialized instruction context.
        - file_serialized_instruction_effects (tuple[str, dict[str, str | None]]): Tuple of file stem and dictionary of target library names and serialized instruction effects.

    Returns:
        - tuple[str, str | None]: Tuple of file stem and instruction fixture.
    """

    file_stem, serialized_instruction_context = file_serialized_instruction_context
    file_stem_2, serialized_instruction_effects = file_serialized_instruction_effects

    assert file_stem == file_stem_2, f"{file_stem} != {file_stem_2}"

    # Both instruction context and instruction effects should not be None
    if serialized_instruction_context is None or serialized_instruction_effects is None:
        return file_stem, None

    _, targets_to_serialized_pruned_instruction_effects = prune_execution_result(
        file_serialized_instruction_context, file_serialized_instruction_effects
    )

    pruned_instruction_effects = targets_to_serialized_pruned_instruction_effects[
        globals.solana_shared_library
    ]

    # Create instruction fixture
    instr_context = pb.InstrContext()
    instr_context.ParseFromString(serialized_instruction_context)
    instr_effects = pb.InstrEffects()
    instr_effects.ParseFromString(pruned_instruction_effects)

    fixture = pb.InstrFixture()
    fixture.input.MergeFrom(instr_context)
    fixture.output.MergeFrom(instr_effects)

    return file_stem, fixture.SerializeToString(deterministic=True)


def write_fixture_to_disk(file_stem: str, serialized_instruction_fixture: str) -> int:
    """
    Writes instruction fixtures to disk.

    Args:
        - file_stem (str): File stem
        - serialized_instruction_fixture (str): Serialized instruction fixture

    Returns:
        - int: 0 on failure, 1 on success
    """
    if serialized_instruction_fixture is None:
        return 0

    with open(f"{globals.output_dir}/{file_stem}.bin", "wb") as f:
        f.write(serialized_instruction_fixture)

    return 1
