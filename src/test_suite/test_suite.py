import shutil
from typing import List
import typer
import ctypes
import filecmp
from glob import glob
import itertools
from pathlib import Path
import subprocess
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
from test_suite.fixture_utils import (
    create_fixture,
    extract_context_from_fixture,
    regenerate_fixture,
)
from test_suite.log_utils import log_results
from test_suite.multiprocessing_utils import (
    decode_single_test_case,
    download_and_process,
    execute_fixture,
    extract_metadata,
    read_fixture,
    initialize_process_output_buffers,
    initialize_process_globals_for_extraction,
    initialize_process_globals_for_decoding,
    initialize_process_globals_for_download,
    initialize_process_globals_for_regeneration,
    process_target,
    run_test,
    read_context,
)
import test_suite.globals as globals
from test_suite.util import (
    set_ld_preload_asan,
    deduplicate_fixtures_by_hash,
    download_progress_bars,
    fetch_with_retries,
    process_items,
)
import resource
import tqdm
from test_suite.fuzz_context import *
import json
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import test_suite.features_utils as features_utils
import traceback
import httpx
from test_suite.fuzzcorp_auth import get_fuzzcorp_auth, FuzzCorpAuth
from test_suite.fuzzcorp_api_client import FuzzCorpAPIClient
from test_suite.fuzzcorp_utils import fuzzcorp_api_call

"""
Harness options:
- InstrHarness
- TxnHarness
- BlockHarness
- SyscallHarness
- ValidateVM
- ElfHarness
"""

app = typer.Typer(help=f"Validate effects from clients using Protobuf messages.")


@app.command(help=f"Execute Context or Fixture message(s) and print the Effects.")
def execute(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input protobuf file or directory of protobuf files",
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help=f"Harness type to use for Context protobufs",
    ),
    shared_library: Path = typer.Option(
        ...,
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    log_level: int = typer.Option(
        2,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    no_print_effects: bool = typer.Option(
        False,
        "--no-print-effects",
        "-n",
        help="Do not print effects to stdout",
    ),
    enable_vm_tracing: bool = typer.Option(
        False,
        "--enable-vm-tracing",
        "-evm",
        help="Enable FD VM tracing",
    ),
):
    # Initialize output buffers and shared library
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)
    if enable_vm_tracing:
        os.environ["ENABLE_VM_TRACING"] = "1"

    try:
        lib = ctypes.CDLL(shared_library)
        lib.sol_compat_init(log_level)
        globals.target_libraries[shared_library] = lib
        globals.reference_shared_library = shared_library
    except:
        set_ld_preload_asan()

    if input.is_file():
        files_to_exec = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        files_to_exec = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    files_to_exec.append(file_path)
    for file in files_to_exec:
        print(f"Handling {file}...")
        if file.suffix == ".fix":
            fn_entrypoint = extract_metadata(file).fn_entrypoint
            harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
            context = read_fixture(file).input
        else:
            harness_ctx = HARNESS_MAP[default_harness_ctx]
            context = read_context(harness_ctx, file)
            if context is None:
                fn_entrypoint = extract_metadata(file).fn_entrypoint
                harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
                context = read_fixture(file).input
        # Execute and cleanup
        start = time.time()
        effects = process_target(harness_ctx, lib, context)
        end = time.time()

        print(f"Total time taken for {file}: {(end - start) * 1000} ms\n------------")

        if not effects:
            print(f"No {harness_ctx.effects_type.__name__} returned")
            continue

        serialized_effects = effects.SerializeToString(deterministic=True)

        # Prune execution results
        serialized_effects = harness_ctx.prune_effects_fn(
            context,
            {shared_library: serialized_effects},
        )[shared_library]

        parsed_instruction_effects = harness_ctx.effects_type()
        parsed_instruction_effects.ParseFromString(serialized_effects)

        # Print human-readable output
        if parsed_instruction_effects:
            harness_ctx.effects_human_encode_fn(parsed_instruction_effects)

        if not no_print_effects:
            print(parsed_instruction_effects)

    lib.sol_compat_fini()
    return True


@app.command(help=f"Extract Context messages from Fixtures.")
def fix_to_ctx(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input Fixture file or directory of Fixture files",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help=f"Output directory for messages",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
):
    # Specify globals
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    if input.is_file():
        test_cases = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        test_cases = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    test_cases.append(file_path)
    num_test_cases = len(test_cases)

    print(f"Converting to Fixture messages...")
    results = process_items(
        test_cases,
        extract_context_from_fixture,
        num_processes=num_processes,
        debug_mode=debug_mode,
        initializer=initialize_process_globals_for_extraction,
        initargs=(output_dir,),
        desc="Converting",
        use_processes=True,
    )

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(results)} total files seen")
    print(f"{sum(results)} files successfully written")
    return True


@app.command(
    help=f"""
             Create test fixtures from a directory of Context and/or Fixture messages.
             Effects are generated by the target passed in with --solana-target or -s.
             You can also pass in additional targets with --target or -t
             and use --keep-passing or -k to only generate effects for test cases that match.
             """
)
def create_fixtures(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input protobuf file or directory of protobuf files",
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help=f"Harness type to use for Context protobufs",
    ),
    reference_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [],
        "--target",
        "-t",
        help="Shared object (.so) target file paths (pairs with --keep-passing)."
        f" Targets must have required function entrypoints defined",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Output directory for fixtures",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    readable: bool = typer.Option(
        False, "--readable", "-r", help="Output fixtures in human-readable format"
    ),
    only_keep_passing: bool = typer.Option(
        False, "--keep-passing", "-k", help="Only keep passing test cases"
    ),
    organize_fixture_dir: bool = typer.Option(
        False, "--group-by-program", "-g", help="Group fixture output by program type"
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
):
    # Add Solana library to shared libraries
    shared_libraries = [reference_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.reference_shared_library = reference_shared_library
    globals.readable = readable
    globals.only_keep_passing = only_keep_passing
    globals.organize_fixture_dir = organize_fixture_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize shared library
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init(log_level)
        globals.target_libraries[target] = lib

    if input.is_file():
        test_cases = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        test_cases = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    test_cases.append(file_path)
    num_test_cases = len(test_cases)

    globals.default_harness_ctx = HARNESS_MAP[default_harness_ctx]

    # Generate the test cases in parallel from files on disk
    print(f"Creating fixtures...")
    write_results = process_items(
        test_cases,
        create_fixture,
        num_processes=num_processes,
        debug_mode=debug_mode,
        initializer=initialize_process_output_buffers,
        desc="Creating fixtures",
        use_processes=True,
    )

    # Clean up
    print("Cleaning up...")
    for target in shared_libraries:
        globals.target_libraries[target].sol_compat_fini()

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")

    # Return success if at least one fixture was written
    return sum(write_results) > 0


@app.command(
    help=f"""
            Run tests on a set of targets with a directory of Context and/or Fixture messages.

            Note: each `.so` target filename must be unique.
            """
)
def run_tests(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input protobuf file or directory of protobuf files",
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help=f"Harness type to use for Context protobufs",
    ),
    reference_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path(os.getenv("FIREDANCER_TARGET", ""))],
        "--target",
        "-t",
        help="Shared object (.so) target file paths",
    ),
    output_dir: Path = typer.Option(
        Path("test_results"),
        "--output-dir",
        "-o",
        help="Output directory for test results",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    log_chunk_size: int = typer.Option(
        10000, "--chunk-size", "-ch", help="Number of test results per file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output: log failed test cases",
    ),
    consensus_mode: bool = typer.Option(
        False,
        "--consensus-mode",
        "-c",
        help="Only fail on consensus failures. One such effect is to normalize error codes when comparing results. \
Note: Cannot be used with --core-bpf-mode or --ignore-compute-units-mode.",
    ),
    core_bpf_mode: bool = typer.Option(
        False,
        "--core-bpf-mode",
        "-cb",
        help="Deliberately skip known mismatches between BPF programs and builtins, only failing on genuine mimatches. \
For example, builtin programs may throw errors on readonly account state violations sooner than BPF programs, \
compute unit usage will be different, etc. This feature is primarily used to test a BPF program against a builtin. \
Note: Cannot be used with --consensus-mode or --ignore-compute-units-mode.",
    ),
    ignore_compute_units_mode: bool = typer.Option(
        False,
        "--ignore-compute-units",
        help="Skip mismatches on only compute units. Good for testing two versions of a BPF program, where one is \
expected to use different amounts of compute units than the other. Note: Cannot be used with --consensus-mode or \
--core-bpf-mode.",
    ),
    failures_only: bool = typer.Option(
        False,
        "--failures-only",
        "-f",
        help="Only log failed test cases",
    ),
    save_failures: bool = typer.Option(
        False,
        "--save-failures",
        "-sf",
        help="Saves failed test cases to results directory",
    ),
    save_successes: bool = typer.Option(
        False,
        "--save-successes",
        "-ss",
        help="Saves successful test cases to results directory",
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
    fail_early: bool = typer.Option(
        False,
        "--fail-early",
        "-fe",
        help="Stop test execution on the first failure",
    ),
):
    # Add Solana library to shared libraries
    shared_libraries = [reference_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.reference_shared_library = reference_shared_library
    globals.default_harness_ctx = HARNESS_MAP[default_harness_ctx]

    # Set diff mode if specified
    if sum([consensus_mode, core_bpf_mode, ignore_compute_units_mode]) > 1:
        typer.echo(
            "Error: --consensus-mode, --core-bpf-mode, and --ignore-compute-units-mode cannot be used together.",
            err=True,
        )
        raise typer.Exit(code=1)
    # Set diff mode to consensus if specified
    globals.consensus_mode = consensus_mode
    # Set diff mode to core_bpf if specified
    globals.core_bpf_mode = core_bpf_mode
    # Set diff mode to ignore_compute_units if specified
    globals.ignore_compute_units_mode = ignore_compute_units_mode

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize shared libraries
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init(log_level)
        globals.target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = globals.output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

    # Collect test cases - recursively search by default
    if input.is_file():
        test_cases = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        test_cases = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    test_cases.append(file_path)

    num_test_cases = len(test_cases)

    # Process the test results in parallel
    print("Running tests...")
    test_case_results = []
    if fail_early:
        # Run tests sequentially and stop on first failure
        initialize_process_output_buffers(randomize_output_buffer)
        for test_case in tqdm.tqdm(test_cases, desc="Running tests"):
            result = run_test(test_case)
            test_case_results.append(result)
            # Check if test failed
            if len(result) >= 2 and result[1] == -1:
                print(
                    f"\nTest failed: {result[0]}. Stopping execution due to --fail-early option."
                )
                break
    else:
        # Use process_items utility for parallel/sequential processing
        test_case_results = process_items(
            items=test_cases,
            process_func=run_test,
            num_processes=num_processes,
            debug_mode=debug_mode,
            initializer=initialize_process_output_buffers,
            initargs=(randomize_output_buffer,),
            desc="Running tests",
            use_processes=True,
        )

    print("Logging results...")
    passed, failed, skipped, target_log_files, failed_tests, skipped_tests = (
        log_results(
            test_cases,
            test_case_results,
            shared_libraries,
            log_chunk_size,
            failures_only,
            save_failures,
            save_successes,
        )
    )

    print("Cleaning up...")
    for target in shared_libraries:
        globals.target_libraries[target].sol_compat_fini()

    peak_memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Peak Memory Usage: {peak_memory_usage_kb / 1024} MB")

    print(f"Total test cases: {passed + failed + skipped}")
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
    if verbose:
        if failed != 0:
            print(f"Failed tests: {failed_tests}")
        if skipped != 0:
            print(f"Skipped tests: {skipped_tests}")
    if failed != 0 and save_failures:
        print("Failures tests are in: ", globals.output_dir / "failed_protobufs")
    print("Successful tests are in: ", globals.output_dir / "successful_protobufs")

    if failed != 0:
        binary_to_log_file = {
            path.stem: log_file.name for path, log_file in target_log_files.items()
        }
        for (name1, file1), (name2, file2) in itertools.combinations(
            binary_to_log_file.items(), 2
        ):
            print(f"Diff between {name1} and {name2}: vimdiff {file1} {file2}")

    success = (failed == 0) and (skipped == 0) and (passed > 0)
    return success


@app.command(help=f"Convert Context and/or Fixture messages to human-readable format.")
def decode_protobufs(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input protobuf file or directory of protobuf files",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help=f"Output directory for base58-encoded, Context and/or Fixture human-readable messages",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help=f"Harness type to use for Context protobufs",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
):
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)
    globals.default_harness_ctx = HARNESS_MAP[default_harness_ctx]

    if input.is_file():
        test_cases = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        test_cases = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    test_cases.append(file_path)
    num_test_cases = len(test_cases)

    write_results = process_items(
        test_cases,
        decode_single_test_case,
        num_processes=num_processes,
        debug_mode=debug_mode,
        initializer=initialize_process_globals_for_decoding,
        initargs=(output_dir, HARNESS_MAP[default_harness_ctx]),
        desc="Decoding",
        use_processes=True,
    )

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")
    return True


@app.command(help=f"List harness types available for use.")
def list_harness_types():
    # pretty print harness types
    print("Available harness types:")
    for name in HARNESS_MAP:
        print(f"- {name}")
    return True


@app.command(help=f"Configure FuzzCorp API credentials (interactive).")
def configure_fuzzcorp(
    force: bool = typer.Option(
        False,
        "--force",
        help="Force reconfiguration even if config exists",
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        help="Clear all cached configuration",
    ),
    validate: bool = typer.Option(
        False,
        "--validate",
        help="Validate current configuration and token",
    ),
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="(No-op, kept for compatibility)",
    ),
):
    """Configure FuzzCorp API credentials interactively or manage configuration."""
    config = FuzzCorpAuth()

    if clear:
        config.clear_all()
        print("Configuration cleared from:", config.config_file)
        return True

    if validate:
        print("Checking configuration...")
        print(f"  API Origin: {config.get_api_origin()}")
        print(f"  Organization: {config.get_organization()}")
        print(f"  Project: {config.get_project()}")

        if config.get_token():
            print(f"  Token: (cached)")
            print("\nValidating token...")
            if config.validate_token():
                print("Token is valid!")
                return True
            else:
                print("Token is invalid or expired")
                print(
                    "\nRun 'solana-conformance configure-fuzzcorp' to re-authenticate."
                )
                raise typer.Exit(code=1)
        else:
            print("No token cached")
            missing_auth = config.get_missing_auth()
            if missing_auth:
                print(f"\nPlease set: {missing_auth}")
            print("\nOr run 'solana-conformance configure-fuzzcorp' to authenticate.")
            raise typer.Exit(code=1)

    # Interactive setup
    if config.interactive_setup(force=force):
        return True
    else:
        print("[ERROR] Configuration setup failed")
        raise typer.Exit(code=1)


@app.command(help=f"List all available repro lineages.")
def list_repros(
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="Use fuzz NG API instead of web scraping",
    ),
    lineage: str = typer.Option(
        None,
        "--lineage",
        "-l",
        help="Filter to specific lineage (shows all repros in that lineage)",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable interactive configuration prompts if credentials are missing",
    ),
    fuzzcorp_url: str = typer.Option(
        os.getenv(
            "FUZZCORP_URL",
            "https://api.dev.fuzzcorp.asymmetric.re/uglyweb/firedancer-io/solfuzz/bugs/",
        ),
        "--fuzzcorp-url",
        "-f",
        help="FuzzCorp URL for web scraping (used when --use-ng is not set)",
    ),
):
    """List all repro lineages with their counts, or all repros in a specific lineage."""

    # Use FuzzCorp HTTP API directly with interactive configuration
    # Get configuration (with interactive prompts if needed)
    config = get_fuzzcorp_auth(interactive=interactive)
    if not config:
        raise typer.Exit(code=1)

    # Fetch repros using the API wrapper
    print(f"Fetching repro index from {config.get_api_origin()}...")

    def fetch_repros(client):
        return client.list_repros()

    response = fuzzcorp_api_call(config, fetch_repros, interactive=interactive)

    # Display the results in a nice table format
    print(f"\nBundle ID: {response.bundle_id}\n")

    if lineage:
        # Show all repros in the specified lineage
        if lineage not in response.lineages:
            print(f"[ERROR] Lineage '{lineage}' not found")
            print(f"\nAvailable lineages:")
            for name in sorted(response.lineages.keys()):
                print(f"  - {name}")
            raise typer.Exit(code=1)

        repros = response.lineages[lineage]
        print(f"Lineage: {lineage}")
        print(f"Total repros: {len(repros)}\n")

        # Print header
        print(f"{'HASH':<70} {'COUNT':<8} {'VERIFIED':<10} {'CREATED':<20}")
        print("─" * 110)

        # Print each repro
        for repro in sorted(repros, key=lambda r: r.created_at, reverse=True):
            verified_str = "Yes" if repro.all_verified else "No"
            created_str = (
                repro.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if repro.created_at
                else "N/A"
            )
            print(
                f"{repro.hash:<70} {repro.count:<8} {verified_str:<10} {created_str:<20}"
            )

        verified_count = sum(1 for r in repros if r.all_verified)
        print(f"\nTotal: {len(repros)} repro(s), {verified_count} verified")
    else:
        # Print each lineage in a table
        print(f"{'LINEAGE':<40} {'COUNT':<10} {'VERIFIED':<10}")
        print("─" * 60)

        for lineage_name, repros in sorted(response.lineages.items()):
            total_count = sum(r.count for r in repros)
            verified_count = sum(r.count for r in repros if r.all_verified)
            print(f"{lineage_name:<40} {total_count:<10} {verified_count:<10}")

        print(f"\nFound {len(response.lineages)} lineage(s).")

    return True


@app.command(help="Download fixtures for a single repro hash from FuzzCorp NG.")
def download_fixture(
    repro_hash: str = typer.Argument(
        ...,
        help="Hash of the repro to download",
    ),
    lineage: str = typer.Option(
        ...,
        "--lineage",
        "-l",
        help="Lineage name (e.g., sol_vm_syscall_cpi_rust_diff_hf)",
    ),
    output_dir: Path = typer.Option(
        Path("./fuzzcorp_downloads"),
        "--output-dir",
        "-o",
        help="Output directory for downloaded repro",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for authentication if needed",
    ),
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="(No-op, kept for compatibility)",
    ),
):
    """Download and extract fixture(s) for a single repro hash from FuzzCorp NG API."""
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)

    inputs_dir = output_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    # Set globals for download_and_process
    globals.output_dir = output_dir
    globals.inputs_dir = inputs_dir

    try:
        # Get configuration
        config = get_fuzzcorp_auth(interactive=interactive)
        if not config:
            print("[ERROR] Failed to authenticate with FuzzCorp API")
            raise typer.Exit(code=1)

        print(
            f"\nDownloading fixture(s) for repro {repro_hash} from lineage {lineage}...\n"
        )

        # Download the repro
        result = download_and_process((lineage, repro_hash))

        # Handle result
        if isinstance(result, dict):
            if result.get("success"):
                print(f"Success!")
                print(f"   Repro: {result['repro']}")
                print(f"   Artifacts: {result.get('artifacts', 0)}")
                print(f"   Fixtures: {result.get('fixtures', 0)}")
            else:
                print(f"[ERROR] Failed: {result['message']}")
                raise typer.Exit(code=1)
        else:
            # Legacy string result
            if result.startswith("Error") or result.startswith("Failed"):
                print(f"[ERROR] {result}")
                raise typer.Exit(code=1)
            else:
                print(f"{result}")

        # Show output location
        supported_extensions = get_all_supported_extensions()
        actual_fixtures = sum(
            len(list(inputs_dir.glob(f"*{ext}"))) for ext in supported_extensions
        )
        print(f"   Total fixtures on disk: {actual_fixtures}")
        print(f"   Output directory: {output_dir}")
        print(f"   Fixtures directory: {inputs_dir}")

    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP request failed: {e}")
        if hasattr(e, "response") and e.response:
            print(f"[ERROR] Response: {e.response.text}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[ERROR] Failed to download fixtures: {e}")
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(
    help="Download fixtures for verified repros in specified lineages from FuzzCorp NG."
)
def download_fixtures(
    output_dir: Path = typer.Option(
        Path("./fuzzcorp_downloads"),
        "--output-dir",
        "-o",
        help="Output directory for downloaded repros",
    ),
    section_names: str = typer.Option(
        ...,
        "--section-names",
        "-n",
        help="Comma-delimited list of lineage names to download",
    ),
    section_limit: int = typer.Option(
        0,
        "--section-limit",
        "-l",
        help="Limit number of repros per lineage (0 = all verified)",
    ),
    num_processes: int = typer.Option(
        4,
        "--num-processes",
        "-p",
        help="Number of parallel download processes",
    ),
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="Use fuzz NG CLI (fuzz list/download repro) instead of API scraping",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for authentication if needed",
    ),
    all_artifacts: bool = typer.Option(
        False,
        "--all-artifacts",
        help="Download all artifacts per repro (default: only latest)",
    ),
):
    """Download and extract fixtures for verified repros from FuzzCorp NG API."""
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)

    inputs_dir = output_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    # Set globals for download_and_process
    globals.output_dir = output_dir
    globals.inputs_dir = inputs_dir
    globals.download_all_artifacts = all_artifacts

    try:
        # Get configuration
        config = get_fuzzcorp_auth(interactive=interactive)
        if not config:
            print("[ERROR] Failed to authenticate with FuzzCorp API")
            raise typer.Exit(code=1)

        # Create HTTP client and fetch repros
        section_names_list = section_names.split(",")
        download_list = []

        # Fetch all repros using API wrapper
        print(f"Fetching repro index ...")

        def fetch_repros(client):
            return client.list_repros()

        response = fuzzcorp_api_call(config, fetch_repros, interactive=interactive)
        print(f"Bundle ID: {response.bundle_id}\n")

        # Process each requested lineage
        for section_name in section_names_list:
            section_name = section_name.strip()
            print(f"Processing lineage: {section_name}")

            # Get repros for this lineage
            lineage_repros = response.lineages.get(section_name, [])
            if not lineage_repros:
                print(f"  [WARNING] No repros found for lineage {section_name}")
                continue

            # Filter to verified repros only
            verified_repros = [r for r in lineage_repros if r.all_verified]

            if section_limit > 0:
                verified_repros = verified_repros[:section_limit]

            if len(verified_repros) == 0:
                print(f"  [WARNING] No verified repros found for {section_name}")
                continue

            # Add to download list
            for repro in verified_repros:
                download_list.append((section_name, repro.hash))

            print(f"  Found {len(verified_repros)} verified repro(s)")

        if not download_list:
            print("\n[ERROR] No repros to download")
            raise typer.Exit(code=1)

        # Prefetch all repro metadata per lineage (more efficient than global or per-hash)
        print(f"\nFetching metadata for all repros...")

        metadata_cache = {}
        with FuzzCorpAPIClient(
            api_origin=config.get_api_origin(),
            token=config.get_token(),
            org=config.get_organization(),
            project=config.get_project(),
            http2=True,
        ) as client:
            # Fetch metadata per lineage (server can efficiently filter per lineage)
            download_hashes = {hash_val for _, hash_val in download_list}
            lineages_to_fetch = {lineage for lineage, _ in download_list}

            for lineage in lineages_to_fetch:
                lineage_repros = client.list_repros_full(
                    lineage=lineage,
                )
                print(f"  Fetched {len(lineage_repros)} repro(s) for lineage {lineage}")
                for repro in lineage_repros:
                    if repro.hash in download_hashes:
                        metadata_cache[repro.hash] = repro
                        # Log artifact count for this repro
                        print(
                            f"    Repro {repro.hash[:8]}: {len(repro.artifact_hashes)} artifact(s)"
                        )

        print(f"  Cached metadata for {len(metadata_cache)} repro(s)\n")

        # Store metadata cache in globals so workers can access it
        globals.repro_metadata_cache = metadata_cache

        print(f"Downloading {len(download_list)} repro(s)...\n")

        with download_progress_bars(len(download_list), "repro") as item_pbar:
            results = process_items(
                items=download_list,
                process_func=download_and_process,
                num_processes=num_processes,
                initializer=initialize_process_globals_for_download,
                initargs=(output_dir, inputs_dir, metadata_cache),
                shared_progress_bar=item_pbar,
            )

        total_artifacts = 0
        total_fixtures = 0
        total_downloaded = 0
        total_cached = 0
        for result in results:
            if isinstance(result, dict):
                if result.get("success"):
                    total_artifacts += result.get("artifacts", 0)
                    total_fixtures += result.get("fixtures", 0)
                    total_downloaded += result.get("downloaded", 0)
                    total_cached += result.get("cached", 0)
                else:
                    print(f"  [WARNING] {result['repro']}: {result['message']}")
            else:
                if result.startswith("Error") or result.startswith("Failed"):
                    print(f"  [WARNING] {result}")

        # Count fixtures and summarize results
        supported_extensions = get_all_supported_extensions()
        actual_fixtures = sum(
            len(list(inputs_dir.glob(f"*{ext}"))) for ext in supported_extensions
        )
        successful = sum(
            1
            for r in results
            if (isinstance(r, dict) and r.get("success"))
            or (isinstance(r, str) and r.startswith("Processed"))
        )
        failed = len(results) - successful

        print(f"\nDownload complete!")
        print(
            f"   Total artifacts: {total_artifacts} ({total_downloaded} downloaded, {total_cached} cached)"
        )
        print(f"   Total fixtures: {actual_fixtures}")
        print(f"   Successful: {successful}/{len(download_list)}")
        if failed > 0:
            print(f"   Failed: {failed}")
        print(f"   Output directory: {output_dir}")
        print(f"   Fixtures directory: {inputs_dir}")

    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP request failed: {e}")
        if hasattr(e, "response") and e.response:
            print(f"[ERROR] Response: {e.response.text}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[ERROR] Failed to download fixtures: {e}")
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(help="Download a single .crash file by hash from FuzzCorp NG.")
def download_crash(
    repro_hash: str = typer.Argument(
        ...,
        help="Hash of the repro to download (.crash)",
    ),
    lineage: str = typer.Option(
        ...,
        "--lineage",
        "-l",
        help="Lineage name (e.g., sol_vm_syscall_cpi_rust_diff_hf)",
    ),
    output_dir: Path = typer.Option(
        Path("./fuzzcorp_downloads"),
        "--output-dir",
        "-o",
        help="Output directory for downloaded crash",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for authentication if needed",
    ),
):
    """Download a single .crash (repro) file from FuzzCorp NG API."""
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    crashes_dir = output_dir / "crashes" / lineage
    crashes_dir.mkdir(parents=True, exist_ok=True)

    # Auth/config
    config = get_fuzzcorp_auth(interactive=interactive)
    if not config:
        print("[ERROR] Failed to authenticate with FuzzCorp API")
        raise typer.Exit(code=1)

    try:
        with FuzzCorpAPIClient(
            api_origin=config.get_api_origin(),
            token=config.get_token(),
            org=config.get_organization(),
            project=config.get_project(),
            http2=True,
        ) as client:
            print(f"Downloading crash {repro_hash} from lineage {lineage}...")
            data = client.download_repro_data(
                repro_hash,
                lineage,
                desc=f"Downloading {repro_hash[:8]}.crash",
            )
            out_path = crashes_dir / f"{repro_hash}.crash"
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"Saved: {out_path}")
    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP request failed: {e}")
        if hasattr(e, "response") and e.response:
            print(f"[ERROR] Response: {e.response.text}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[ERROR] Failed to download crash: {e}")
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(help="Download .crash files for specified lineages from FuzzCorp NG.")
def download_crashes(
    output_dir: Path = typer.Option(
        Path("./fuzzcorp_downloads"),
        "--output-dir",
        "-o",
        help="Output directory for downloaded crashes",
    ),
    section_names: str = typer.Option(
        ...,
        "--section-names",
        "-n",
        help="Comma-delimited list of lineage names to download",
    ),
    section_limit: int = typer.Option(
        0,
        "--section-limit",
        "-l",
        help="Limit number of crashes per lineage (0 = all verified)",
    ),
    num_processes: int = typer.Option(
        4,
        "--num-processes",
        "-p",
        help="Number of parallel download processes",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for authentication if needed",
    ),
):
    """Download raw .crash files (repros) for given lineages."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auth/config
    config = get_fuzzcorp_auth(interactive=interactive)
    if not config:
        print("[ERROR] Failed to authenticate with FuzzCorp API")
        raise typer.Exit(code=1)

    try:
        # List all repros
        print("Fetching repro index ...")

        def fetch_repros(client):
            return client.list_repros()

        response = fuzzcorp_api_call(config, fetch_repros, interactive=interactive)

        # Prepare worker globals and task list
        globals.output_dir = output_dir
        download_list = []
        for lineage in [s.strip() for s in section_names.split(",") if s.strip()]:
            lineage_repros = response.lineages.get(lineage, [])
            if not lineage_repros:
                print(f"[WARNING] No repros found for lineage {lineage}")
                continue
            verified = [r for r in lineage_repros if r.all_verified]
            if section_limit > 0:
                verified = verified[:section_limit]
            if not verified:
                print(f"[WARNING] No verified repros for {lineage}")
                continue
            for repro in verified:
                download_list.append((lineage, repro.hash))

        # Prefetch metadata for all selected hashes per lineage (for consistency and potential reuse)
        if download_list:
            print("\nFetching metadata for selected repros...")
            from test_suite.fuzzcorp_api_client import FuzzCorpAPIClient as _FCA

            metadata_cache = {}
            with _FCA(
                api_origin=config.get_api_origin(),
                token=config.get_token(),
                org=config.get_organization(),
                project=config.get_project(),
                http2=True,
            ) as client:
                selection = {h for _, h in download_list}
                lineages_to_fetch = {lineage for lineage, _ in download_list}

                for lineage in lineages_to_fetch:
                    lineage_repros = client.list_repros_full(
                        lineage=lineage,
                    )
                    print(
                        f"  Fetched {len(lineage_repros)} repro(s) for lineage {lineage}"
                    )
                    for repro in lineage_repros:
                        if repro.hash in selection:
                            metadata_cache[repro.hash] = repro
                            print(
                                f"    Repro {repro.hash[:8]}: {len(repro.artifact_hashes)} artifact(s)"
                            )
            globals.repro_metadata_cache = metadata_cache

        from test_suite.multiprocessing_utils import download_single_crash

        print(f"Downloading {len(download_list)} crash file(s) ...")

        with download_progress_bars(len(download_list), "crash") as item_pbar:
            results = process_items(
                items=download_list,
                process_func=download_single_crash,
                num_processes=num_processes,
                debug_mode=False,
                initializer=initialize_process_globals_for_download,
                initargs=(output_dir, None, metadata_cache),
                shared_progress_bar=item_pbar,
            )

        total = len(download_list)
        saved = sum(
            1 for r in results if isinstance(r, dict) and r.get("downloaded", 0) == 1
        )
        cached = sum(
            1 for r in results if isinstance(r, dict) and r.get("cached", 0) == 1
        )
        failed = total - (saved + cached)

        print(
            f"\nDownload complete: saved {saved}, cached {cached}, failed {failed} (total {total})"
        )
        print(f"Output directory: {output_dir}")
    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP request failed: {e}")
        if hasattr(e, "response") and e.response:
            print(f"[ERROR] Response: {e.response.text}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[ERROR] Failed to download crashes: {e}")
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(
    help=f"""
            Run tests on a set of targets with a list of FuzzCorp mismatch links.

            Note: each `.so` target filename must be unique.
            """
)
def debug_mismatches(
    reference_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help=f"Harness type to use for Context protobufs",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path(os.getenv("FIREDANCER_TARGET", ""))],
        "--target",
        "-t",
        help="Shared object (.so) target file paths (pairs with --keep-passing)."
        f" Targets must have required function entrypoints defined",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help=f"Output directory for messages",
    ),
    repro_urls: str = typer.Option(
        "", "--repro-urls", "-u", help="Comma-delimited list of FuzzCorp mismatch links"
    ),
    section_names: str = typer.Option(
        "",
        "--section-names",
        "-n",
        help="Comma-delimited list of FuzzCorp section names",
    ),
    fuzzcorp_url: str = typer.Option(
        os.getenv(
            "FUZZCORP_URL",
            "https://api.dev.fuzzcorp.asymmetric.re/uglyweb/firedancer-io/solfuzz/bugs/",
        ),
        "--fuzzcorp-url",
        "-f",
        help="Comma-delimited list of FuzzCorp section names",
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    section_limit: int = typer.Option(
        0, "--section-limit", "-l", help="Limit number of fixture per section"
    ),
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="Use fuzz NG CLI (fuzz list/download repro) instead of API scraping",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
    all_artifacts: bool = typer.Option(
        False,
        "--all-artifacts",
        help="Download all artifacts per repro (default: only latest)",
    ),
):
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)

    globals.output_dir = output_dir
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    globals.inputs_dir = globals.output_dir / "inputs"
    globals.inputs_dir.mkdir(parents=True, exist_ok=True)
    globals.download_all_artifacts = all_artifacts

    fuzzcorp_cookie = os.getenv("FUZZCORP_COOKIE")
    repro_urls_list = repro_urls.split(",") if repro_urls else []
    section_names_list = section_names.split(",") if section_names else []

    custom_data_urls = []
    # Use FuzzCorp HTTP API to list repros
    # Get configuration (interactive if needed)
    config = get_fuzzcorp_auth(interactive=True)
    if not config:
        print("[ERROR] Failed to authenticate with FuzzCorp API")
        raise typer.Exit(code=1)

    # Fetch all repros using API wrapper
    print(f"Fetching repro index from {config.get_api_origin()}...")

    def fetch_repros(client):
        return client.list_repros()

    response = fuzzcorp_api_call(config, fetch_repros, interactive=True)

    # Process each requested lineage
    for section_name in section_names_list:
        print(f"Fetching crashes for lineage {section_name} ...")

        # Get repros for this lineage
        lineage_repros = response.lineages.get(section_name, [])
        if not lineage_repros:
            print(f"No repros found for lineage {section_name}")
            continue

        # Filter to verified repros only
        verified_repros = [r for r in lineage_repros if r.all_verified]

        if section_limit != 0:
            verified_repros = verified_repros[:section_limit]

        if len(verified_repros) == 0:
            print(f"No verified repros found for {section_name}")
            continue

        # Add to download list
        for repro in verified_repros:
            custom_data_urls.append((section_name, repro.hash))

        print(f"Found {len(verified_repros)} verified repro(s) for {section_name}")

    ld_preload = os.environ.pop("LD_PRELOAD", None)

    num_test_cases = len(custom_data_urls)
    metadata_cache = None

    if num_test_cases > 0:
        print(f"Fetching metadata for all repros...")

        metadata_cache = {}
        with FuzzCorpAPIClient(
            api_origin=config.get_api_origin(),
            token=config.get_token(),
            org=config.get_organization(),
            project=config.get_project(),
            http2=True,
        ) as client:
            # Fetch metadata per lineage (server can efficiently filter per lineage)
            download_hashes = {hash_val for _, hash_val in custom_data_urls}
            lineages_to_fetch = {lineage for lineage, _ in custom_data_urls}

            for lineage in lineages_to_fetch:
                lineage_repros = client.list_repros_full(
                    lineage=lineage,
                )
                print(f"  Fetched {len(lineage_repros)} repro(s) for lineage {lineage}")
                for repro in lineage_repros:
                    if repro.hash in download_hashes:
                        metadata_cache[repro.hash] = repro
                        print(
                            f"    Repro {repro.hash[:8]}: {len(repro.artifact_hashes)} artifact(s)"
                        )

        print(f"  Cached metadata for {len(metadata_cache)} repro(s)")

        if len(metadata_cache) == 0 and num_test_cases > 0:
            print(
                f"  [WARNING] Failed to prefetch metadata. Will fetch individually per repro."
            )
            print(f"  [WARNING] This will be significantly slower and may timeout.")
            print(f"  [WARNING] The FuzzCorp API may be in a degraded state.\n")
        else:
            print()

        globals.repro_metadata_cache = metadata_cache

    print(f"Downloading {num_test_cases} tests...")

    with download_progress_bars(num_test_cases, "repro") as item_pbar:
        results = process_items(
            custom_data_urls,
            download_and_process,
            num_processes=num_processes,
            debug_mode=debug_mode,
            initializer=initialize_process_globals_for_download,
            initargs=(output_dir, globals.inputs_dir, metadata_cache),
            shared_progress_bar=item_pbar,
        )

    # Print download results summary
    successful_downloads = [r for r in results if r and r.get("success")]
    failed_downloads = [r for r in results if r and not r.get("success")]
    print(
        f"\nDownload summary: {len(successful_downloads)} succeeded, {len(failed_downloads)} failed"
    )

    if failed_downloads:
        print(f"\n[WARNING] Failed downloads:")
        for failure in failed_downloads:
            print(
                f"  - {failure.get('repro', 'unknown')}: {failure.get('message', 'unknown error')}"
            )

    if ld_preload is not None:
        os.environ["LD_PRELOAD"] = ld_preload

    repro_custom = globals.output_dir / "repro_custom"
    if repro_custom.exists():
        shutil.rmtree(repro_custom)

    # Count only actual files, not directories
    files = [f for f in Path(globals.inputs_dir).iterdir() if f.is_file()]

    if not files:
        print(f"\n[ERROR] No fixtures were downloaded. Cannot proceed.")
        print(f"This usually means the repros don't have artifacts attached yet.")
        raise typer.Exit(code=1)

    print(f"Deduplicating {len(files)} downloaded fixture(s)...")
    num_duplicates = deduplicate_fixtures_by_hash(globals.inputs_dir)
    if num_duplicates > 0:
        print(f"Removed {num_duplicates} duplicate(s)")

    create_fixtures_dir = globals.output_dir / "create_fixtures"
    if create_fixtures_dir.exists():
        shutil.rmtree(create_fixtures_dir)
    create_fixtures_dir.mkdir(parents=True, exist_ok=True)

    run_tests_output = globals.output_dir / "test_results"

    create_fixtures(
        input=globals.inputs_dir,
        default_harness_ctx=default_harness_ctx,
        reference_shared_library=reference_shared_library,
        shared_libraries=shared_libraries,
        output_dir=create_fixtures_dir,
        num_processes=num_processes,
        readable=False,
        only_keep_passing=False,
        organize_fixture_dir=False,
        log_level=log_level,
        debug_mode=debug_mode,
    )

    shutil.rmtree(globals.inputs_dir)
    shutil.copytree(create_fixtures_dir, globals.inputs_dir)
    shutil.rmtree(create_fixtures_dir)

    return run_tests(
        input=globals.inputs_dir,
        reference_shared_library=reference_shared_library,
        default_harness_ctx=default_harness_ctx,
        shared_libraries=shared_libraries,
        output_dir=run_tests_output,
        num_processes=num_processes,
        randomize_output_buffer=False,
        log_chunk_size=10000,
        verbose=True,
        consensus_mode=False,
        core_bpf_mode=False,
        ignore_compute_units_mode=False,
        failures_only=False,
        save_failures=True,
        save_successes=True,
        log_level=log_level,
        debug_mode=debug_mode,
        fail_early=False,
    )


@app.command(help="Debug a single repro by hash.")
def debug_mismatch(
    repro_hash: str = typer.Argument(
        ...,
        help="Hash of the repro to debug",
    ),
    lineage: str = typer.Option(
        ...,
        "--lineage",
        "-l",
        help="Lineage name (e.g., sol_vm_syscall_cpi_rust_diff_hf)",
    ),
    reference_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path(os.getenv("FIREDANCER_TARGET", ""))],
        "--target",
        "-t",
        help="Shared object (.so) target file paths to test against reference",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Output directory for test results",
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help="Harness type to use for Context protobufs",
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        help="FD logging level",
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for authentication if needed",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode for detailed output",
    ),
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="(No-op, kept for compatibility)",
    ),
):
    """Debug a single repro by downloading and testing it."""
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)

    globals.output_dir = output_dir

    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    globals.inputs_dir = globals.output_dir / "inputs"
    if globals.inputs_dir.exists():
        shutil.rmtree(globals.inputs_dir)
    globals.inputs_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Get configuration
        config = get_fuzzcorp_auth(interactive=interactive)
        if not config:
            print("[ERROR] Failed to authenticate with FuzzCorp API")
            raise typer.Exit(code=1)

        print(f"\nDownloading repro {repro_hash} from lineage {lineage}...")

        # Download the repro
        result = download_and_process((lineage, repro_hash))

        # Handle result
        if isinstance(result, dict):
            if not result.get("success"):
                print(f"[ERROR] Download failed: {result['message']}")
                raise typer.Exit(code=1)
            print(
                f"Downloaded {result.get('fixtures', 0)} fixture(s) from {result.get('artifacts', 0)} artifact(s)\n"
            )
        else:
            # Legacy string result
            if result.startswith("Error") or result.startswith("Failed"):
                print(f"[ERROR] {result}")
                raise typer.Exit(code=1)
            print(f"{result}\n")

        # Deduplicate
        print("Deduplicating fixtures...")
        num_duplicates = deduplicate_fixtures_by_hash(globals.inputs_dir)
        if num_duplicates > 0:
            print(f"Removed {num_duplicates} duplicate(s)")

        # Create fixtures
        create_fixtures_dir = globals.output_dir / "create_fixtures"
        if create_fixtures_dir.exists():
            shutil.rmtree(create_fixtures_dir)
        create_fixtures_dir.mkdir(parents=True, exist_ok=True)

        run_tests_output = globals.output_dir / "test_results"

        print("Creating fixtures...")
        create_fixtures(
            input=globals.inputs_dir,
            default_harness_ctx=default_harness_ctx,
            reference_shared_library=reference_shared_library,
            shared_libraries=shared_libraries,
            output_dir=create_fixtures_dir,
            num_processes=1,  # Single repro, no need for parallel
            readable=False,
            only_keep_passing=False,
            organize_fixture_dir=False,
            log_level=log_level,
            debug_mode=debug_mode,
        )

        print("Running tests...")
        run_tests(
            input=create_fixtures_dir,
            default_harness_ctx=default_harness_ctx,
            reference_shared_library=reference_shared_library,
            shared_libraries=shared_libraries,
            output_dir=run_tests_output,
            num_processes=1,  # Single repro, no need for parallel
            randomize_output_buffer=randomize_output_buffer,
            log_chunk_size=10000,
            verbose=True,  # Verbose for single repro debugging
            consensus_mode=False,
            core_bpf_mode=False,
            ignore_compute_units_mode=False,
            save_failures=True,
            save_successes=True,
            log_level=log_level,
            debug_mode=debug_mode,
            fail_early=False,
        )

        # Show results
        print(f"\nResults:")
        print(f"   Output directory: {output_dir}")
        print(f"   Fixtures directory: {globals.inputs_dir}")
        print(f"   Test results: {run_tests_output}")

        # Show vimdiff command if there are failures
        failed_protobufs = run_tests_output / "failed_protobufs"
        if failed_protobufs.exists() and list(failed_protobufs.glob("*")):
            libsolfuzz = run_tests_output / "libsolfuzz_agave"
            libfd = run_tests_output / "libfd_exec_sol_compat"
            first_failure = next(failed_protobufs.glob("*")).stem
            print(f"\nTo view differences:")
            print(
                f"   vimdiff {libsolfuzz}/{first_failure}.txt {libfd}/{first_failure}.txt"
            )

    except Exception as e:
        print(f"[ERROR] Failed to debug repro: {e}")
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(
    help=f"""
        Regenerate features in fixture messages.
    """
)
def regenerate_fixtures(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Either a file or directory containing messages",
    ),
    shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Output directory for regenerated fixtures",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Only print the fixtures that would be regenerated",
    ),
    add_features: List[str] = typer.Option(
        [],
        "--add-feature",
        "-f",
        help="List of feature pubkeys to force add to the fixtures.",
    ),
    remove_features: List[str] = typer.Option(
        [],
        "--remove-feature",
        "-r",
        help="List of feature pubkeys to force remove from the fixtures.",
    ),
    rekeyed_features: List[str] = typer.Option(
        [],
        "--rekey-feature",
        "-k",
        help="List of feature pubkeys to rekey in the fixtures, formatted 'old/new' (e.g. `--rekey-feature old/new`).",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output: print filenames that will be regenerated",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
):
    globals.output_dir = output_dir
    globals.reference_shared_library = shared_library

    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    lib: ctypes.CDLL = ctypes.CDLL(shared_library)
    lib.sol_compat_init(log_level)
    globals.target_libraries[shared_library] = lib
    initialize_process_output_buffers()

    if input.is_file():
        test_cases = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        test_cases = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    test_cases.append(file_path)
    num_regenerated = 0

    globals.features_to_add = set(
        map(features_utils.feature_bytes_to_ulong, add_features)
    )
    globals.features_to_remove = set(
        map(features_utils.feature_bytes_to_ulong, remove_features)
    )
    globals.target_features = features_utils.get_sol_compat_features_t(lib)
    globals.rekey_features = list(
        tuple(map(features_utils.feature_bytes_to_ulong, feature.split("/")))
        for feature in rekeyed_features
    )

    globals.regenerate_dry_run = dry_run
    globals.regenerate_verbose = verbose

    results = process_items(
        test_cases,
        regenerate_fixture,
        num_processes=num_processes,
        debug_mode=debug_mode,
        initializer=initialize_process_globals_for_regeneration,
        initargs=(
            output_dir,
            shared_library,
            shared_library,
            log_level,
            globals.features_to_add,
            globals.features_to_remove,
            globals.rekey_features,
            dry_run,
            verbose,
        ),
        desc="Regenerating",
        use_processes=True,
    )
    num_regenerated = sum(results)

    lib.sol_compat_fini()
    print(f"Regenerated {num_regenerated} / {len(test_cases)} fixtures")
    return True


@app.command(
    help=f"""
        Regenerate features for fixtures in provided test-vectors folder.
    """
)
def mass_regenerate_fixtures(
    test_vectors: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input test-vectors directory",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Output directory for regenerated fixtures",
    ),
    shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    add_features: List[str] = typer.Option(
        [],
        "--add-feature",
        "-f",
        help="List of feature pubkeys to force add to the fixtures.",
    ),
    remove_features: List[str] = typer.Option(
        [],
        "--remove-feature",
        "-r",
        help="List of feature pubkeys to force remove from the fixtures.",
    ),
    rekeyed_features: List[str] = typer.Option(
        [],
        "--rekey-feature",
        "-k",
        help="List of feature pubkeys to rekey in the fixtures, formatted 'old/new' (e.g. `--rekey-feature old/new`).",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Only print the fixtures that would be regenerated",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output: print filenames that will be regenerated",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        help="Enables debug mode, which disables multiprocessing",
    ),
):
    globals.output_dir = output_dir

    if output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    def copy_files_excluding_fixture_files(src, dst):
        regenerate_folders = set()
        fixtures_folders = glob(str(src) + "/*/fixtures*")
        for root, dirs, files in os.walk(src):
            src_dir = os.path.join(src, os.path.relpath(root, src))
            dest_dir = os.path.join(dst, os.path.relpath(root, src))

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            if not any(
                root.startswith(fixture_folder) for fixture_folder in fixtures_folders
            ):
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dst_file)
            else:
                if files:
                    regenerate_folders.add(src_dir)
        return regenerate_folders

    def get_harness_type_for_folder(src, regenerate_folder):
        relative_path = os.path.relpath(regenerate_folder, src)
        fuzz_folder = relative_path.split(os.sep)[0]
        capitalized_name = "".join(word.capitalize() for word in fuzz_folder.split("_"))
        harness_name = capitalized_name + "Harness"
        return harness_name

    regenerate_folders = copy_files_excluding_fixture_files(test_vectors, output_dir)
    for source_folder in regenerate_folders:
        globals.target_libraries = {}
        output_folder = os.path.join(
            output_dir, os.path.relpath(source_folder, test_vectors)
        )
        folder_harness_type = get_harness_type_for_folder(test_vectors, source_folder)
        print(
            f"Regenerating fixtures for {source_folder} with harness type {folder_harness_type}"
        )
        regenerate_fixtures(
            input=Path(source_folder),
            shared_library=shared_library,
            output_dir=Path(output_folder),
            dry_run=dry_run,
            add_features=add_features,
            remove_features=remove_features,
            rekeyed_features=rekeyed_features,
            num_processes=num_processes,
            verbose=verbose,
            log_level=5,
            debug_mode=debug_mode,
        )

    print(f"Regenerated fixtures from {test_vectors} to {output_dir}")
    return True


@app.command(
    help=f"""
        Execute fixtures and check for correct effects
    """
)
def exec_fixtures(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help=f"Input protobuf file or directory of protobuf files",
    ),
    shared_library: Path = typer.Option(
        ...,
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Output directory for test results",
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    log_level: int = typer.Option(
        2,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    failures_only: bool = typer.Option(
        False,
        "--failures-only",
        "-f",
        help="Only log failed test cases",
    ),
    save_failures: bool = typer.Option(
        False,
        "--save-failures",
        "-sf",
        help="Saves failed test cases to results directory",
    ),
    save_successes: bool = typer.Option(
        False,
        "--save-successes",
        "-ss",
        help="Saves successful test cases to results directory",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which spawns a single child process for easier debugging",
    ),
):
    # Specify globals
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Make expected and actual results directories
    (globals.output_dir / "expected").mkdir(parents=True, exist_ok=True)
    (globals.output_dir / "actual").mkdir(parents=True, exist_ok=True)

    # Initialize output buffers and shared library
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)
    try:
        lib = ctypes.CDLL(shared_library)
        lib.sol_compat_init(log_level)
        globals.target_libraries[shared_library] = lib
        globals.reference_shared_library = shared_library
    except:
        set_ld_preload_asan()

    if input.is_file():
        test_cases = [input]
    else:
        # Recursively find all files in the directory with supported extensions
        test_cases = []
        supported_extensions = get_all_supported_extensions()
        for ext in supported_extensions:
            for file_path in input.rglob(f"*{ext}"):
                if file_path.is_file():
                    test_cases.append(file_path)
    num_test_cases = len(test_cases)
    print("Running tests...")
    test_case_results = process_items(
        test_cases,
        execute_fixture,
        num_processes=num_processes,
        debug_mode=debug_mode,
        initializer=initialize_process_output_buffers,
        initargs=(randomize_output_buffer,),
        desc="Running tests",
        use_processes=True,
    )

    print("Logging results...")
    passed, failed, skipped, target_log_files, failed_tests, skipped_tests = (
        log_results(
            test_cases,
            test_case_results,
            [Path("expected"), Path("actual")],
            10000,
            failures_only,
            save_failures,
            save_successes,
        )
    )

    lib.sol_compat_fini()

    print(f"Total test cases: {passed + failed + skipped}")
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
    if failed != 0:
        print(f"Failed tests: {failed_tests}")
    if skipped != 0:
        print(f"Skipped tests: {skipped_tests}")

    return (failed == 0) and (skipped == 0) and (passed > 0)


@app.command(
    help=f"""
            Set up environment for debugging a mismatch from FuzzCorp
            """
)
def create_env(
    reference_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    default_harness_ctx: str = typer.Option(
        "InstrHarness",
        "--default-harness-type",
        "-h",
        help=f"Harness type to use for Context protobufs",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path(os.getenv("FIREDANCER_TARGET", ""))],
        "--target",
        "-t",
        help="Shared object (.so) target file paths (pairs with --keep-passing)."
        f" Targets must have required function entrypoints defined",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help=f"Output directory for messages",
    ),
    repro_urls: str = typer.Option(
        "", "--repro-urls", "-u", help="Comma-delimited list of FuzzCorp mismatch links"
    ),
    section_names: str = typer.Option(
        "",
        "--section-names",
        "-n",
        help="Comma-delimited list of FuzzCorp section names",
    ),
    fuzzcorp_url: str = typer.Option(
        os.getenv(
            "FUZZCORP_URL",
            "https://api.dev.fuzzcorp.asymmetric.re/uglyweb/firedancer-io/solfuzz/bugs/",
        ),
        "--fuzzcorp-url",
        "-f",
        help="Comma-delimited list of FuzzCorp section names",
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        "-l",
        help="FD logging level",
    ),
    randomize_output_buffer: bool = typer.Option(
        False,
        "--randomize-output-buffer",
        "-r",
        help="Randomizes bytes in output buffer before shared library execution",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
    section_limit: int = typer.Option(
        0, "--section-limit", "-l", help="Limit number of fixture per section"
    ),
    firedancer_repo_path: Path = typer.Option(
        os.getenv("FIREDANCER_DIR"),
        "--firedancer-repo",
        "-fd",
        help="Path to firedancer repository",
    ),
    test_vectors_repos_path: Path = typer.Option(
        os.getenv("TEST_VECTORS_DIR"),
        "--test-vectors-repo",
        "-tv",
        help="Path to test-vectors repository",
    ),
    use_ng: bool = typer.Option(
        True,
        "--use-ng",
        help="Use fuzz NG CLI (fuzz list/download repro) instead of API scraping",
    ),
    debug_mode: bool = typer.Option(
        False,
        "--debug-mode",
        "-d",
        help="Enables debug mode, which disables multiprocessing",
    ),
):
    lists = [
        f"{file.parent.name}/{file.name}"
        for file in firedancer_repo_path.glob(
            "contrib/test/test-vectors-fixtures/*fixtures*/*list"
        )
    ]

    max_width = max(len(option) for option in lists) + 2

    print("Select correct list for mismatch:")
    for i, option in enumerate(lists, start=1):
        print(f"{i}. {option}".ljust(max_width), end="\t")
        if i % 4 == 0:
            print()

    if len(lists) % 4 != 0:
        print()

    while True:
        try:
            choice = int(input("Enter the list of your choice: "))
            if 1 <= choice <= len(lists):
                selected_option = lists[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(lists)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    print(f"Adding fixture to: {selected_option}")
    list_path = glob(
        str(firedancer_repo_path)
        + f"/contrib/test/test-vectors-fixtures/{selected_option}"
    )[0]

    print("Running debug_mismatches to test fixtures...")
    passed = debug_mismatches(
        reference_shared_library=reference_shared_library,
        default_harness_ctx=default_harness_ctx,
        shared_libraries=shared_libraries,
        output_dir=output_dir,
        repro_urls=repro_urls,
        section_names=section_names,
        fuzzcorp_url=fuzzcorp_url,
        log_level=log_level,
        randomize_output_buffer=randomize_output_buffer,
        num_processes=num_processes,
        section_limit=section_limit,
        use_ng=use_ng,
        debug_mode=debug_mode,
    )

    if passed:
        print("All fixtures already pass")
        raise typer.Exit(code=0)

    failures = glob(str(output_dir) + "/test_results/failed_protobufs/*")

    print(
        f"Adding {len(failures)} failed test(s) to {list_path} and copying to test vectors repository..."
    )
    for failure in failures:
        with open(list_path, "r") as file:
            lines = file.readlines()

        last_line = lines[-1].strip()

        failure_path = os.path.dirname(last_line) + "/" + os.path.basename(failure)
        with open(list_path, "a") as file:
            file.write(failure_path + "\n")
        print(f"\nAdded {os.path.basename(failure)} to {list_path}")

        failure_test_vector_path = failure_path.replace(
            "dump/test-vectors", str(test_vectors_repos_path)
        )
        shutil.copy2(failure, os.path.dirname(failure_test_vector_path))
        print(f"Copied to {os.path.dirname(failure_test_vector_path)}")

    print(f"Successfully processed {len(failures)} failed test(s)")
    print(f"Updated list file: {list_path}")
    print(f"Copied fixtures to: {test_vectors_repos_path}")
    return True


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Run the fuzzcorp 'fuzz' binary with the provided arguments.",
)
def fuzz(
    ctx: typer.Context,
):
    """
    Pass-through command to run the fuzzcorp 'fuzz' binary.

    This command looks for the 'fuzz' binary in:
    1. FUZZCORP_FUZZ_BINARY environment variable (if set)
    2. System PATH

    All arguments after 'fuzz' are passed directly to the binary.

    Examples:
        ./solana-conformance fuzz help
        ./solana-conformance fuzz version
        ./solana-conformance fuzz list repros --org myorg --project myproject

    Note: Use 'fuzz help' instead of 'fuzz --help' to get the fuzz binary's help.
    """
    # Check for FUZZCORP_FUZZ_BINARY environment variable
    fuzz_binary = os.getenv("FUZZCORP_FUZZ_BINARY")
    if fuzz_binary:
        if not os.path.exists(fuzz_binary):
            print(
                f"[ERROR] FUZZCORP_FUZZ_BINARY is set but file not found: {fuzz_binary}"
            )
            raise typer.Exit(code=1)
        if not os.access(fuzz_binary, os.X_OK):
            print(
                f"[ERROR] FUZZCORP_FUZZ_BINARY is set but file is not executable: {fuzz_binary}"
            )
            raise typer.Exit(code=1)
    else:
        # Look for 'fuzz' in PATH
        fuzz_binary = shutil.which("fuzz")
        if not fuzz_binary:
            print("[ERROR] 'fuzz' binary not found in PATH")
            print("\nPlease either:")
            print("  1. Add the 'fuzz' binary to your PATH, or")
            print("  2. Set FUZZCORP_FUZZ_BINARY environment variable to the full path")
            print("\nExample:")
            print("  export FUZZCORP_FUZZ_BINARY=/path/to/fuzz")
            raise typer.Exit(code=1)

    # Build command with all extra arguments
    cmd = [fuzz_binary] + ctx.args

    # Run the fuzz binary with all arguments
    try:
        result = subprocess.run(cmd, check=False)
        raise typer.Exit(code=result.returncode)
    except FileNotFoundError:
        print(f"[ERROR] Failed to execute: {fuzz_binary}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        raise typer.Exit(code=130)


if __name__ == "__main__":
    app()
