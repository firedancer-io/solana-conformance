from test_suite.constants import OUTPUT_BUFFER_SIZE
import test_suite.invoke_pb2 as pb
from test_suite.instr.codec_utils import encode_input, encode_output, decode_input
from test_suite.instr.validation_utils import check_account_unchanged, is_valid
import ctypes
from test_suite.sol_compat import exec_sol_compat_call, process_target

from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format


def lazy_starmap(args, function):
    return function(*args)


def process_instruction(
    library: ctypes.CDLL,
    serialized_instruction_context: str,
) -> pb.InstrEffects | None:

    output_data = exec_sol_compat_call(
        library,
        "sol_compat_instr_execute_v1",
        serialized_instruction_context,
    )

    output_object = pb.InstrEffects()
    output_object.ParseFromString(output_data)
    return output_object


def generate_test_case(test_file: Path) -> tuple[str, str | None]:
    """
    Reads in test files and generates an InstrContext Protobuf object for a test case.

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - tuple[str, str | None]: Tuple of file stem and serialized instruction context, if exists.
    """
    # Try to read in first as binary-encoded Protobuf messages
    try:
        # Read in binary Protobuf messages
        with open(test_file, "rb") as f:
            instruction_context = globals.harness_ctx.context_type()
            instruction_context.ParseFromString(f.read())
    except:
        try:
            # Maybe it's in human-readable Protobuf format?
            with open(test_file) as f:
                instruction_context = text_format.Parse(
                    f.read(), globals.harness_ctx.context_type()
                )

            # Decode into digestable fields
            decode_input(instruction_context)
        except:
            # Unable to read message, skip and continue
            instruction_context = None

    if instruction_context is None:
        # Unreadable file, skip it
        return test_file.stem, None

    # Discard unknown fields
    instruction_context.DiscardUnknownFields()

    # Serialize instruction context to string (pickleable)
    return test_file.stem, instruction_context.SerializeToString(deterministic=True)


def decode_single_test_case(test_file: Path) -> int:
    """
    Decode a single test case into a human-readable message

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - int: 1 if successfully decoded and written, 0 if skipped.
    """
    _, serialized_instruction_context = generate_test_case(test_file)

    # Skip if input is invalid
    if serialized_instruction_context is None:
        return 0

    # Encode the input fields to be human readable
    instruction_context = pb.InstrContext()
    instruction_context.ParseFromString(serialized_instruction_context)
    encode_input(instruction_context)

    with open(globals.output_dir / (test_file.stem + ".txt"), "w") as f:
        f.write(
            text_format.MessageToString(instruction_context, print_unknown_fields=False)
        )
    return 1


def process_single_test_case(
    file_stem: str, serialized_instruction_context: str | None
) -> tuple[str, dict[str, str | None] | None]:
    """
    Process a single execution context (file, serialized instruction context) through
    all target libraries and returns serialized instruction effects. This
    function is called by processes.

    Args:
        - file_stem (str): Stem of file containing serialized instruction context.
        - serialized_instruction_context (str | None): Serialized instruction context.

    Returns:
        - tuple[str, dict[str, str | None] | None]: Tuple of file stem and dictionary of target library names
            and instruction effects.
    """
    # Mark as skipped if instruction context doesn't exist
    if serialized_instruction_context is None:
        return file_stem, None

    # Execute test case on each target library
    results = {}
    for target in globals.target_libraries:
        instruction_effects = process_target(
            globals.target_libraries[target],
            serialized_instruction_context,
            globals.harness_ctx,
        )
        result = (
            instruction_effects.SerializeToString(deterministic=True)
            if instruction_effects
            else None
        )
        results[target] = result

    return file_stem, results


def merge_results_over_iterations(results: tuple) -> tuple[str, dict]:
    """
    Merge results over separate iterations for a single test case.

    Args:
        - results (tuple): Tuple of (file stem, result for each target) for each iteration for a single test case.

    Returns:
        - tuple[str, dict]: Tuple of file stem and merged results over all iterations for single test case.
    """
    file = None
    merged_results = {}
    for target in globals.target_libraries:
        merged_results[target] = {}

        for iteration in range(globals.n_iterations):
            file_stem, execution_result = results[iteration]
            file = file_stem

            if execution_result is None:
                merged_results[target][iteration] = None
                continue

            merged_results[target][iteration] = execution_result[target]

    return file, merged_results


def prune_execution_result(
    file_serialized_instruction_context: tuple[str, str],
    file_serialized_instruction_effects: tuple[str, dict[str, str | None]],
) -> tuple[str, dict]:
    """
    Prune execution result to only include actually modified accounts.

    Args:
        - file_serialized_instruction_context (tuple[str, str]): Tuple of file stem and serialized instruction context.
        - file_serialized_instruction_effects (tuple[str, dict[str, str | None]]): Tuple of file stem and dictionary of target library names and serialized instruction effects.

    Returns:
        - tuple[str, dict]: Tuple of file stem and serialized pruned instruction effects for each target.
    """
    file_stem, serialized_instruction_context = file_serialized_instruction_context
    if serialized_instruction_context is None:
        return file_stem, None

    instruction_context = pb.InstrContext()
    instruction_context.ParseFromString(serialized_instruction_context)

    file_stem_2, targets_to_serialized_instruction_effects = (
        file_serialized_instruction_effects
    )
    assert file_stem == file_stem_2, f"{file_stem}, {file_stem_2}"

    targets_to_serialized_pruned_instruction_effects = {}
    for (
        target,
        serialized_instruction_effects,
    ) in targets_to_serialized_instruction_effects.items():
        if serialized_instruction_effects is None:
            targets_to_serialized_pruned_instruction_effects[target] = None
            continue

        instruction_effects = pb.InstrEffects()
        instruction_effects.ParseFromString(serialized_instruction_effects)

        # O(n^2) because not performance sensitive
        new_modified_accounts: list[pb.AcctState] = []
        for modified_account in instruction_effects.modified_accounts:
            account_unchanged = False
            for beginning_account_state in instruction_context.accounts:
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

    return file_stem, targets_to_serialized_pruned_instruction_effects


def check_consistency_in_results(file_stem: str, results: dict) -> dict[str, bool]:
    """
    Check consistency for all target libraries over all iterations for a test case.

    Args:
        - file_stem (str): File stem of the test case.
        - execution_results (dict): Dictionary of target library names and serialized instruction effects.

    Returns:
        - dict[str, bool]: For each target name, 1 if passed, -1 if failed, 0 if skipped.
    """
    if results is None:
        return {target: 0 for target in globals.target_libraries}

    results_per_target = {}
    for target in globals.target_libraries:
        protobuf_structures = {}
        for iteration in range(globals.n_iterations):
            # Create a Protobuf struct to compare and output, if applicable
            protobuf_struct = None
            if results[target][iteration]:
                # Turn bytes into human readable fields
                protobuf_struct = pb.InstrEffects()
                protobuf_struct.ParseFromString(results[target][iteration])
                encode_output(protobuf_struct)

            protobuf_structures[iteration] = protobuf_struct

            # Write output Protobuf struct to logs
            with open(
                globals.output_dir
                / target.stem
                / str(iteration)
                / (file_stem + ".txt"),
                "w",
            ) as f:
                if protobuf_struct:
                    f.write(text_format.MessageToString(protobuf_struct))
                else:
                    f.write(str(None))

        test_case_passed = all(
            protobuf_structures[iteration] == protobuf_structures[0]
            for iteration in range(globals.n_iterations)
        )
        results_per_target[target] = 1 if test_case_passed else -1

    return results_per_target


def build_test_results(
    file_stem: str, results: dict[str, str | None]
) -> tuple[str, int, dict | None]:
    """
    Build a single result of single test execution and returns whether the test passed or failed.

    Args:
        - file_stem (str): File stem of the test case.
        - results (dict[str, str | None]): Dictionary of target library names and serialized instruction effects.

    Returns:
        - tuple[str, int, dict | None]: Tuple of:
            - File stem
            - 1 if passed, -1 if failed, 0 if skipped
            - Dictionary of target library names and file-dumpable serialized instruction effects
    """
    # If no results or Agave rejects input, mark case as skipped
    if results is None:
        # Mark as skipped (0)
        return file_stem, 0, None

    outputs = {target: "None\n" for target in results}

    # Log execution results
    protobuf_structures = {}
    for target, result in results.items():
        # Create a Protobuf struct to compare and output, if applicable
        instruction_effects = None
        if result:
            # Turn bytes into human readable fields
            instruction_effects = pb.InstrEffects()
            instruction_effects.ParseFromString(result)
            encode_output(instruction_effects)
            outputs[target] = text_format.MessageToString(instruction_effects)

        protobuf_structures[target] = instruction_effects

    test_case_passed = all(
        protobuf_structures[globals.reference_shared_library] == result
        for result in protobuf_structures.values()
    )

    # 1 = passed, -1 = failed
    return file_stem, 1 if test_case_passed else -1, outputs


def run_test(test_file: Path) -> tuple[str, int, dict | None]:
    """
    Runs a single test from start to finish.

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - tuple[str, int, dict | None]: Tuple of:
            - File stem
            - 1 if passed, -1 if failed, 0 if skipped
            - Dictionary of target library names and file-dumpable serialized instruction effects
    """
    test_case = generate_test_case(test_file)
    results = process_single_test_case(*test_case)
    pruned_results = prune_execution_result(test_case, results)
    return build_test_results(*pruned_results)
