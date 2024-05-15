from test_suite.codec_utils import encode_input, encode_output
from test_suite.multiprocessing_utils import prune_execution_result
import test_suite.globals as globals
import test_suite.invoke_pb2 as pb
from google.protobuf import text_format
from pathlib import Path


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

    if pruned_instruction_effects is None:
        return file_stem, None

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
    Writes instruction fixtures to disk. This function outputs in binary format unless
    specified otherwise with the --readable flag.

    Args:
        - file_stem (str): File stem
        - serialized_instruction_fixture (str): Serialized instruction fixture

    Returns:
        - int: 0 on failure, 1 on success
    """
    if serialized_instruction_fixture is None:
        return 0

    if globals.readable:
        # Deserialize fixture
        instr_fixture = pb.InstrFixture()
        instr_fixture.ParseFromString(serialized_instruction_fixture)

        # Encode fields for instruction context and effects
        instr_context = pb.InstrContext()
        instr_context.CopyFrom(instr_fixture.input)
        encode_input(instr_context)

        instr_effects = pb.InstrEffects()
        instr_effects.CopyFrom(instr_fixture.output)
        encode_output(instr_effects)

        instr_fixture.input.CopyFrom(instr_context)
        instr_fixture.output.CopyFrom(instr_effects)

        with open(globals.output_dir / (file_stem + ".fix.txt"), "w") as f:
            f.write(
                text_format.MessageToString(instr_fixture, print_unknown_fields=False)
            )
    else:
        with open(f"{globals.output_dir}/{file_stem}.fix", "wb") as f:
            f.write(serialized_instruction_fixture)

    return 1


def extract_instr_context_from_fixture(fixture_file: Path):
    """
    Extract InstrContext from InstrEffects and write to disk.

    Args:
        - fixture_file (Path): Path to fixture file

    Returns:
        - int: 1 on success, 0 on failure
    """
    try:
        instr_fixture = pb.InstrFixture()
        with open(fixture_file, "rb") as f:
            instr_fixture.ParseFromString(f.read())

        with open(globals.output_dir / (fixture_file.stem + ".bin"), "wb") as f:
            f.write(instr_fixture.input.SerializeToString(deterministic=True))
    except:
        return 0

    return 1
