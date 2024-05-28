from dataclasses import dataclass, field
from test_suite.constants import OUTPUT_BUFFER_SIZE
import test_suite.invoke_pb2 as pb
from test_suite.validation_utils import check_account_unchanged
import ctypes
from ctypes import c_uint64, c_int, POINTER, Structure
from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format
import os


def process_target(
    library: ctypes.CDLL, serialized_instruction_context: str
) -> pb.InstrEffects | None:
    """
    Process an instruction through a provided shared library and return the result.

    Args:
        - library (ctypes.CDLL): Shared library to process instructions.
        - serialized_instruction_context (str): Serialized instruction context message.

    Returns:
        - pb.InstrEffects | None: Result of instruction execution.
    """

    # Define argument and return types
    library.sol_compat_instr_execute_v1.argtypes = [
        POINTER(ctypes.c_uint8),  # out_ptr
        POINTER(c_uint64),  # out_psz
        POINTER(ctypes.c_uint8),  # in_ptr
        c_uint64,  # in_sz
    ]
    library.sol_compat_instr_execute_v1.restype = c_int

    # Prepare input data and output buffers
    in_data = serialized_instruction_context
    in_ptr = (ctypes.c_uint8 * len(in_data))(*in_data)
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(OUTPUT_BUFFER_SIZE)

    # Call the function
    sol_compat_fn = getattr(library, globals.harness_ctx.fuzz_fn_name)
    result = sol_compat_fn(
        globals.output_buffer_pointer, ctypes.byref(out_sz), in_ptr, in_sz
    )

    # Result == 0 means execution failed
    if result == 0:
        return None

    # Process the output
    output_data = bytearray(globals.output_buffer_pointer[: out_sz.value])
    output_object = pb.InstrEffects()
    output_object.ParseFromString(output_data)

    return output_object


def read_context(test_file: Path) -> str | None:
    """
    Reads in test files and generates an InstrContext Protobuf object for a test case.

    Args:
        - test_file (Path): Path to the instruction context message.

    Returns:
        - str | None: Serialized instruction context, or None if reading failed.
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
            # decode_input(instruction_context)
            globals.harness_ctx.context_human_decode_fn(instruction_context)
        except:
            # Unable to read message, skip and continue
            instruction_context = None

    if instruction_context is None:
        # Unreadable file, skip it
        return None

    # Discard unknown fields
    instruction_context.DiscardUnknownFields()

    # Serialize instruction context to string (pickleable)
    return instruction_context.SerializeToString(deterministic=True)


def read_fixture(fixture_file: Path) -> str | None:
    """
    Same as read_instr, but for InstrFixture protobuf messages.

    DOES NOT SUPPORT HUMAN READABLE MESSAGES!!!

    Args:
        - fixture_file (Path): Path to the instruction fixture message.

    Returns:
        - str | None: Serialized instruction fixture, or None if reading failed.
    """
    # Try to read in first as binary-encoded Protobuf messages
    try:
        # Read in binary Protobuf messages
        with open(fixture_file, "rb") as f:
            instruction_fixture = globals.harness_ctx.fixture_type()
            instruction_fixture.ParseFromString(f.read())
    except:
        # Unable to read message, skip and continue
        instruction_fixture = None

    if instruction_fixture is None:
        # Unreadable file, skip it
        return None

    # Discard unknown fields
    instruction_fixture.DiscardUnknownFields()

    # Serialize instruction fixture to string (pickleable)
    return instruction_fixture.SerializeToString(deterministic=True)


def decode_single_test_case(test_file: Path) -> int:
    """
    Decode a single test case into a human-readable message

    Args:
        - test_file (Path): Path to the file containing serialized instruction contexts.

    Returns:
        - int: 1 if successfully decoded and written, 0 if skipped.
    """
    serialized_instruction_context = read_context(test_file)

    # Skip if input is invalid
    if serialized_instruction_context is None:
        return 0

    # Encode the input fields to be human readable
    instruction_context = globals.harness_ctx.context_type()
    instruction_context.ParseFromString(serialized_instruction_context)
    globals.harness_ctx.context_human_encode_fn(instruction_context)

    with open(globals.output_dir / (test_file.stem + ".txt"), "w") as f:
        f.write(
            text_format.MessageToString(instruction_context, print_unknown_fields=False)
        )
    return 1


def process_single_test_case(
    serialized_instruction_context: str | None,
) -> dict[str, str | None] | None:
    """
    Process a single execution context (file, serialized instruction context) through
    all target libraries and returns serialized instruction effects.

    Args:
        - serialized_instruction_context (str | None): Serialized instruction context.

    Returns:
        - dict[str, str | None] | None: Dictionary of target library names and instruction effects.
    """
    # Mark as skipped if instruction context doesn't exist
    if serialized_instruction_context is None:
        return None

    # Execute test case on each target library
    results = {}
    for target in globals.target_libraries:
        instruction_effects = process_target(
            globals.target_libraries[target], serialized_instruction_context
        )
        result = (
            instruction_effects.SerializeToString(deterministic=True)
            if instruction_effects
            else None
        )
        results[target] = result

    return results


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
    serialized_context: str,
    targets_to_serialized_effects: dict[str, str | None],
) -> dict[str, str | None] | None:
    """
    Prune execution result to only include actually modified accounts.

    Args:
        - serialized_instruction_context (str): Serialized instruction context.
        - serialized_instruction_effects (dict[str, str | None]): Dictionary of target library names and serialized instruction effects.

    Returns:
        - dict[str, str | None] | None: Serialized pruned instruction effects for each target.
    """
    if serialized_context is None:
        return None

    EffectsT = globals.harness_ctx.effects_type

    if not hasattr(EffectsT(), "modified_accounts"):
        # no execution results to prune
        # TODO: perform this check in a more robust way
        return targets_to_serialized_effects

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

        instruction_effects = EffectsT()
        instruction_effects.ParseFromString(serialized_instruction_effects)

        # O(n^2) because not performance sensitive
        new_modified_accounts: list[pb.AcctState] = []
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
                protobuf_struct = globals.harness_ctx.effects_type()
                protobuf_struct.ParseFromString(results[target][iteration])
                globals.harness_ctx.effects_human_encode_fn(protobuf_struct)

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


def build_test_results(results: dict[str, str | None]) -> tuple[int, dict | None]:
    """
    Build a single result of single test execution and returns whether the test passed or failed.

    Args:
        - results (dict[str, str | None]): Dictionary of target library names and serialized instruction effects.

    Returns:
        - tuple[int, dict | None]: Tuple of:
            - 1 if passed, -1 if failed, 0 if skipped
            - Dictionary of target library names and file-dumpable serialized instruction effects
    """
    # If no results or Agave rejects input, mark case as skipped
    if results is None:
        # Mark as skipped (0)
        return 0, None

    outputs = {target: "None\n" for target in results}

    # Log execution results
    protobuf_structures = {}
    for target, result in results.items():
        # Create a Protobuf struct to compare and output, if applicable
        instruction_effects = None
        if result is not None:
            # Turn bytes into human readable fields
            instruction_effects = globals.harness_ctx.effects_type()
            instruction_effects.ParseFromString(result)
            globals.harness_ctx.effects_human_encode_fn(instruction_effects)
            outputs[target] = text_format.MessageToString(instruction_effects)

        protobuf_structures[target] = instruction_effects

    if protobuf_structures[globals.solana_shared_library] is None:
        return 0, None

    diff_effect_fn = globals.harness_ctx.diff_effect_fn
    test_case_passed = all(
        diff_effect_fn(protobuf_structures[globals.solana_shared_library], result)
        for result in protobuf_structures.values()
    )

    # 1 = passed, -1 = failed
    return 1 if test_case_passed else -1, outputs


def initialize_process_output_buffers(randomize_output_buffer=False):
    """
    Initialize shared memory and pointers for output buffers for each process.

    Args:
        - randomize_output_buffer (bool): Whether to randomize output buffer.
    """
    globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)()

    if randomize_output_buffer:
        output_buffer_random_bytes = os.urandom(OUTPUT_BUFFER_SIZE)
        globals.output_buffer_pointer = (ctypes.c_uint8 * OUTPUT_BUFFER_SIZE)(
            *output_buffer_random_bytes
        )


@dataclass
class FeaturePool:
    supported: list[int] = field(default_factory=list)
    hardcoded: list[int] = field(default_factory=list)


class sol_compat_features_t(Structure):
    _fields_ = [
        ("struct_size", c_uint64),
        ("hardcoded_features", POINTER(c_uint64)),
        ("hardcoded_feature_cnt", c_uint64),
        ("supported_features", POINTER(c_uint64)),
        ("supported_feature_cnt", c_uint64),
    ]


def get_feature_pool(library: ctypes.CDLL) -> FeaturePool:
    library.sol_compat_get_features_v1.argtypes = None
    library.sol_compat_get_features_v1.restype = POINTER(sol_compat_features_t)

    result = library.sol_compat_get_features_v1().contents
    if result.struct_size < 40:
        raise ValueError("sol_compat_get_features_v1 not supported")

    supported = [
        result.supported_features[i] for i in range(result.supported_feature_cnt)
    ]
    hardcoded = [
        result.hardcoded_features[i] for i in range(result.hardcoded_feature_cnt)
    ]
    return FeaturePool(supported, hardcoded)


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
    # Process fixtures through this entrypoint as well
    if test_file.suffix == ".fix":
        fixture = globals.harness_ctx.fixture_type()
        fixture.ParseFromString(test_file.open("rb").read())
        serialized_instr_context = fixture.input.SerializeToString(deterministic=True)
    else:
        serialized_instr_context = read_context(test_file)
    results = process_single_test_case(serialized_instr_context)
    pruned_results = prune_execution_result(serialized_instr_context, results)
    return test_file.stem, *build_test_results(pruned_results)
