from dataclasses import dataclass, field
from test_suite.constants import OUTPUT_BUFFER_SIZE
import test_suite.invoke_pb2 as invoke_pb
import ctypes
from ctypes import c_uint64, c_int, POINTER, Structure
from pathlib import Path
import test_suite.globals as globals
from google.protobuf import text_format
import os


def process_target(
    library: ctypes.CDLL, serialized_instruction_context: str
) -> invoke_pb.InstrEffects | None:
    """
    Process an instruction through a provided shared library and return the result.

    Args:
        - library (ctypes.CDLL): Shared library to process instructions.
        - serialized_instruction_context (str): Serialized instruction context message.

    Returns:
        - invoke_pb.InstrEffects | None: Result of instruction execution.
    """
    # Prepare input data and output buffers
    in_data = serialized_instruction_context
    in_ptr = (ctypes.c_uint8 * len(in_data))(*in_data)
    in_sz = len(in_data)
    out_sz = ctypes.c_uint64(OUTPUT_BUFFER_SIZE)

    # Get the function to call
    sol_compat_fn = getattr(library, globals.harness_ctx.fuzz_fn_name)

    # Define argument and return types
    sol_compat_fn.argtypes = [
        POINTER(ctypes.c_uint8),  # out_ptr
        POINTER(c_uint64),  # out_psz
        POINTER(ctypes.c_uint8),  # in_ptr
        c_uint64,  # in_sz
    ]
    sol_compat_fn.restype = c_int

    # Call the function
    result = sol_compat_fn(
        globals.output_buffer_pointer, ctypes.byref(out_sz), in_ptr, in_sz
    )
    # Result == 0 means execution failed
    if result == 0:
        return None

    # Process the output
    output_data = bytearray(globals.output_buffer_pointer[: out_sz.value])
    output_object = globals.harness_ctx.effects_type()
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

    ref_result = results[globals.solana_shared_library]

    if ref_result is None:
        print("Skipping test case due to Agave rejection")
        return 0, None

    ref_effects = globals.harness_ctx.effects_type()
    ref_effects.ParseFromString(ref_result)
    globals.harness_ctx.effects_human_encode_fn(ref_effects)

    # Log execution results
    all_passed = True
    for target, result in results.items():
        if target == globals.solana_shared_library:
            continue
        # Create a Protobuf struct to compare and output, if applicable
        effects = None
        if result is not None:
            # Turn bytes into human readable fields
            effects = globals.harness_ctx.effects_type()
            effects.ParseFromString(result)
            globals.harness_ctx.effects_human_encode_fn(effects)

            # Note: diff_effect_fn may modify effects in-place
            all_passed &= globals.harness_ctx.diff_effect_fn(ref_effects, effects)
            outputs[target] = text_format.MessageToString(effects)
        else:
            all_passed = False

    outputs[globals.solana_shared_library] = text_format.MessageToString(ref_effects)

    # 1 = passed, -1 = failed
    return 1 if all_passed else -1, outputs


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
    pruned_results = globals.harness_ctx.prune_effects_fn(
        serialized_instr_context, results
    )
    return test_file.stem, *build_test_results(pruned_results)
