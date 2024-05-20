import fd58
from test_suite.codec_utils import encode_input, encode_output
from test_suite.constants import NATIVE_PROGRAM_MAPPING
from test_suite.multiprocessing_utils import (
    build_test_results,
    read_instr,
    process_single_test_case,
    prune_execution_result,
)
import test_suite.globals as globals
import test_suite.invoke_pb2 as pb
from google.protobuf import text_format
from pathlib import Path


def create_fixture(test_file: Path) -> int:
    """
    Create instruction fixture for an instruction context and effects.

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts

    Returns:
        - int: 1 on success, 0 on failure
    """
    serialized_instr_context = read_instr(test_file)
    results = process_single_test_case(serialized_instr_context)
    pruned_results = prune_execution_result(serialized_instr_context, results)

    # This is only relevant when you gather results for multiple targets
    if globals.only_keep_passing:
        status, _ = build_test_results(pruned_results)
        if status != 1:
            return 0

    if pruned_results is None:
        return 0

    serialized_instr_effects = pruned_results[globals.solana_shared_library]

    if serialized_instr_context is None or serialized_instr_effects is None:
        return 0

    # Create instruction fixture
    instr_context = pb.InstrContext()
    instr_context.ParseFromString(serialized_instr_context)
    instr_effects = pb.InstrEffects()
    instr_effects.ParseFromString(serialized_instr_effects)

    fixture = pb.InstrFixture()
    fixture.input.MergeFrom(instr_context)
    fixture.output.MergeFrom(instr_effects)

    return write_fixture_to_disk(
        test_file.stem, fixture.SerializeToString(deterministic=True)
    )


def write_fixture_to_disk(file_stem: str, serialized_instruction_fixture: str) -> int:
    """
    Writes instruction fixtures to disk. This function outputs in binary format unless
    specified otherwise with the --readable flag.

    Args:
        - file_stem (str): File stem

    Returns:
        - int: 0 on failure, 1 on success
    """
    if serialized_instruction_fixture is None:
        return 0

    output_dir = globals.output_dir

    if globals.organize_fixture_dir:
        instr_fixture = pb.InstrFixture()
        instr_fixture.ParseFromString(serialized_instruction_fixture)
        program_type = get_program_type(instr_fixture)
        output_dir = output_dir / program_type
        output_dir.mkdir(parents=True, exist_ok=True)

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

        with open(output_dir / (file_stem + ".fix.txt"), "w") as f:
            f.write(
                text_format.MessageToString(instr_fixture, print_unknown_fields=False)
            )
    else:
        with open(output_dir / (file_stem + ".fix"), "wb") as f:
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


def get_program_type(instr_fixture: pb.InstrFixture) -> str:
    """
    Get the program type based on the program / loader id.

    Args:
        - fixture (pb.InstrFixture): Instruction fixture

    Returns:
        - str | None: Program type (unknown if not found)
    """
    # Check if the program type can be deduced from program_id
    program_id = fd58.enc32(instr_fixture.input.program_id).decode()

    program_type = NATIVE_PROGRAM_MAPPING.get(program_id, None)
    if program_type:
        return program_type

    # Use the program_id owner instead (loader_id may not be reliable)
    for account_state in instr_fixture.input.accounts:
        if account_state.address == instr_fixture.input.program_id:
            program_type = NATIVE_PROGRAM_MAPPING.get(
                fd58.enc32(account_state.owner).decode(), "unknown"
            )
            if program_type != "unknown":
                program_type += "-programs"
            return program_type

    return "unknown"
