import shutil
from typing import List
import typer
import ctypes
import filecmp
from glob import glob
import itertools
from multiprocessing import Pool
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
    process_target,
    run_test,
    read_context,
)
import test_suite.globals as globals
from test_suite.util import set_ld_preload_asan
import resource
import tqdm
from test_suite.fuzz_context import *
import json
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import test_suite.features_utils as features_utils

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

    files_to_exec = list(input.iterdir()) if input.is_dir() else [input]
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
):
    # Specify globals
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    test_cases = list(input.iterdir()) if input.is_dir() else [input]
    num_test_cases = len(test_cases)

    print(f"Converting to Fixture messages...")
    results = []
    with Pool(processes=num_processes) as pool:
        for result in tqdm.tqdm(
            pool.imap(extract_context_from_fixture, test_cases),
            total=num_test_cases,
        ):
            results.append(result)

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(results)} total files seen")
    print(f"{sum(results)} files successfully written")


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

    test_cases = [input] if input.is_file() else list(input.iterdir())
    num_test_cases = len(test_cases)

    globals.default_harness_ctx = HARNESS_MAP[default_harness_ctx]

    # Generate the test cases in parallel from files on disk
    print(f"Creating fixtures...")
    write_results = []
    with Pool(
        processes=num_processes, initializer=initialize_process_output_buffers
    ) as pool:
        for result in tqdm.tqdm(
            pool.imap(
                create_fixture,
                test_cases,
            ),
            total=num_test_cases,
        ):
            write_results.append(result)

    # Clean up
    print("Cleaning up...")
    for target in shared_libraries:
        globals.target_libraries[target].sol_compat_fini()

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")


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
        help="Enables debug mode, which disables multiprocessing",
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
        # Recursively find all files in the directory
        test_cases = []
        for file_path in input.rglob("*"):
            if file_path.is_file():
                test_cases.append(file_path)

    num_test_cases = len(test_cases)

    # Process the test results in parallel
    print("Running tests...")
    test_case_results = []
    if num_processes > 1 and not debug_mode:
        with Pool(
            processes=num_processes,
            initializer=initialize_process_output_buffers,
            initargs=(randomize_output_buffer,),
        ) as pool:
            for result in tqdm.tqdm(
                pool.imap(run_test, test_cases),
                total=num_test_cases,
            ):
                test_case_results.append(result)
    else:
        initialize_process_output_buffers(randomize_output_buffer)
        for test_case in tqdm.tqdm(test_cases):
            test_case_results.append(run_test(test_case))

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

    return (failed == 0) and (skipped == 0) and (passed > 0)


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
):
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)
    globals.default_harness_ctx = HARNESS_MAP[default_harness_ctx]

    test_cases = list(input.iterdir()) if input.is_dir() else [input]
    num_test_cases = len(test_cases)

    write_results = []
    with Pool(processes=num_processes) as pool:
        for result in tqdm.tqdm(
            pool.imap(decode_single_test_case, test_cases),
            total=num_test_cases,
        ):
            write_results.append(result)

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")


@app.command(help=f"List harness types available for use.")
def list_harness_types():
    # pretty print harness types
    print("Available harness types:")
    for name in HARNESS_MAP:
        print(f"- {name}")


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
        False,
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
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)

    globals.output_dir = output_dir

    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    globals.inputs_dir = globals.output_dir / "inputs"

    if globals.inputs_dir.exists():
        shutil.rmtree(globals.inputs_dir)
    globals.inputs_dir.mkdir(parents=True, exist_ok=True)

    fuzzcorp_cookie = os.getenv("FUZZCORP_COOKIE")
    repro_urls_list = repro_urls.split(",") if repro_urls else []
    section_names_list = section_names.split(",") if section_names else []

    custom_data_urls = []
    if use_ng:
        fuzz_bin = os.getenv("FUZZ_BIN", "fuzz")
        for section_name in section_names_list:
            print(f"Fetching crashes for lineage {section_name} ...")
            cmd = [
                fuzz_bin,
                "list",
                "repro",
                "--lineage",
                section_name,
                "--json",
                "--verbose",
            ]
            result = subprocess.run(
                cmd, text=True, capture_output=True, check=True, stderr=None
            )
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(
                    f"Error parsing JSON from FuzzCorp NG CLI for {section_name}: {e}"
                )
                continue

            # NG schema: data["Data"] is a list of lineage entries
            lineage_entry = next(
                (
                    item
                    for item in data.get("Data", [])
                    if item.get("LineageName") == section_name
                ),
                None,
            )
            if not lineage_entry:
                print(f"No matching lineage found for {section_name}")
                continue

            repros = lineage_entry.get("Repros", [])
            verified_repros = [r for r in repros if r.get("AllVerified") is True]

            if section_limit != 0:
                verified_repros = verified_repros[:section_limit]

            for repro in verified_repros:
                custom_data_urls.append((section_name, str(repro["Hash"])))
    else:  # legacy FuzzCorp web page scraping
        if len(section_names_list) != 0:
            curl_command = f"curl {fuzzcorp_url} --cookie s={fuzzcorp_cookie}"
            result = subprocess.run(
                curl_command, shell=True, capture_output=True, text=True
            )
            page_content = result.stdout
            soup = BeautifulSoup(page_content, "html.parser")
            for section_name in section_names_list:
                current_section_count = 0
                print(f"Getting links from section {section_name}...")
                lineage_div = soup.find("div", id=f"lin_{section_name}")

                if lineage_div:
                    tables = lineage_div.find_all("table")
                    if len(tables) > 1:
                        issues_table = tables[1]
                        hrefs = [
                            link["href"]
                            for link in issues_table.find_all("a", href=True)
                        ]
                        for href in hrefs:
                            if (
                                section_limit != 0
                                and current_section_count >= section_limit
                            ):
                                break
                            repro_urls_list.append(urljoin(fuzzcorp_url, href))
                            current_section_count += 1
                    else:
                        print(f"No bugs found for section {section_name}.")
                else:
                    print(f"Section {section_name} not found.")

        for url in repro_urls_list:
            result = subprocess.run(
                ["curl", "--cookie", f"s={fuzzcorp_cookie}", f"{url}.bash"],
                capture_output=True,
                text=True,
            )
            start_index = result.stdout.find("REPRO_CUSTOM_URL=")
            end_index = result.stdout.find("\n", start_index)
            custom_url = result.stdout[
                start_index + len("REPRO_CUSTOM_URL=") + 1 : end_index - 1
            ].strip()
            if custom_url == "":
                print(f"Failed to get custom URL from {url}")
                continue
            custom_data_urls.append(custom_url)

    ld_preload = os.environ.pop("LD_PRELOAD", None)

    num_test_cases = len(custom_data_urls)
    print("Downloading tests...")
    results = []
    if num_processes > 1 and not debug_mode:
        with Pool(
            processes=num_processes,
            initializer=initialize_process_output_buffers,
            initargs=(randomize_output_buffer,),
        ) as pool:
            for result in tqdm.tqdm(
                pool.imap(download_and_process, custom_data_urls),
                total=num_test_cases,
            ):
                results.append(result)
    else:
        initialize_process_output_buffers(randomize_output_buffer)
        for url in tqdm.tqdm(custom_data_urls):
            results.append(download_and_process(url))

    if ld_preload is not None:
        os.environ["LD_PRELOAD"] = ld_preload

    repro_custom = globals.output_dir / "repro_custom"
    if repro_custom.exists():
        shutil.rmtree(repro_custom)

    files = glob(str(globals.inputs_dir) + "/*")

    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            if (
                os.path.exists(files[i])
                and os.path.exists(files[j])
                and filecmp.cmp(files[i], files[j], shallow=False)
            ):
                os.remove(files[j])

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
    )


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
    regenerate_all: bool = typer.Option(
        False,
        "--regenerate-all",
        "-a",
        help="Regenerate all fixtures, regardless of feature set changes",
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

    test_cases = list(input.iterdir()) if input.is_dir() else [input]
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

    globals.regenerate_all = regenerate_all
    globals.regenerate_dry_run = dry_run
    globals.regenerate_verbose = verbose

    with Pool(
        processes=num_processes,
        initializer=initialize_process_output_buffers,
    ) as pool:
        for result in tqdm.tqdm(
            pool.imap(regenerate_fixture, test_cases),
            total=len(test_cases),
        ):
            num_regenerated += result

    lib.sol_compat_fini()
    print(f"Regenerated {num_regenerated} / {len(test_cases)} fixtures")


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
    regenerate_all: bool = typer.Option(
        False,
        "--regenerate-all",
        "-a",
        help="Regenerate all fixtures, regardless of feature set changes",
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
        if folder_harness_type in ["ElfLoaderHarness"]:
            shutil.copytree(source_folder, output_folder, dirs_exist_ok=True)
        else:
            regenerate_fixtures(
                input=Path(source_folder),
                shared_library=shared_library,
                output_dir=Path(output_folder),
                dry_run=dry_run,
                add_features=add_features,
                remove_features=remove_features,
                rekeyed_features=rekeyed_features,
                regenerate_all=regenerate_all,
                num_processes=num_processes,
                verbose=verbose,
                log_level=5,
            )

    print(f"Regenerated fixtures from {test_vectors} to {output_dir}")


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
        help="Enables debug mode, which disables multiprocessing",
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

    test_cases = list(input.iterdir()) if input.is_dir() else [input]
    num_test_cases = len(test_cases)
    print("Running tests...")
    test_case_results = []

    if num_processes > 1 and not debug_mode:
        with Pool(
            processes=num_processes,
            initializer=initialize_process_output_buffers,
            initargs=(randomize_output_buffer,),
        ) as pool:
            for result in tqdm.tqdm(
                pool.imap(execute_fixture, test_cases),
                total=num_test_cases,
            ):
                test_case_results.append(result)
    else:
        initialize_process_output_buffers(randomize_output_buffer)
        for test_case in tqdm.tqdm(test_cases):
            test_case_results.append(execute_fixture(test_case))

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
        False,
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
        typer.Exit(code=1)

    failures = glob(str(output_dir) + "/test_results/failed_protobufs/*")

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


if __name__ == "__main__":
    app()
