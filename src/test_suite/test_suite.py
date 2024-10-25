import shutil
from typing import List
import typer
from collections import defaultdict
import ctypes
from glob import glob
from multiprocessing import Pool
from pathlib import Path
import subprocess
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
from test_suite.fixture_utils import (
    create_fixture,
    create_fixture_from_context,
    extract_context_from_fixture,
    write_fixture_to_disk,
)
from test_suite.multiprocessing_utils import (
    decode_single_test_case,
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
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import test_suite.features_utils as features_utils
import test_suite.context_pb2 as context_pb
import test_suite.pb_utils as pb_utils

"""
Harness options:
- InstrHarness
- TxnHarness
- SyscallHarness
- ValidateVM
- ElfHarness
"""

app = typer.Typer(help=f"Validate effects from clients using Protobuf messages.")


@app.command(help=f"Execute Context or Fixture message(s) and print the Effects.")
def execute(
    input: Path = typer.Option(
        None,
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
        Path("impl/firedancer/build/native/clang/lib/libfd_exec_sol_compat.so"),
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
):
    # Initialize output buffers and shared library
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)
    try:
        lib = ctypes.CDLL(shared_library)
        lib.sol_compat_init(log_level)
        globals.target_libraries[shared_library] = lib
        globals.reference_shared_library = shared_library
    except:
        set_ld_preload_asan()

    files_to_exec = input.iterdir() if input.is_dir() else [input]
    for file in files_to_exec:
        print(f"Handling {file}...")
        if file.suffix == ".fix":
            fn_entrypoint = extract_metadata(file).fn_entrypoint
            harness_ctx = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
            context = read_fixture(file).input
        else:
            harness_ctx = HARNESS_MAP[default_harness_ctx]
            context = read_context(harness_ctx, file)

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

        print(parsed_instruction_effects)

    lib.sol_compat_fini()


@app.command(help=f"Extract Context messages from Fixtures.")
def fix_to_ctx(
    input: Path = typer.Option(
        Path("fixtures"),
        "--input",
        "-i",
        help=f"Input Fixture file or directory of Fixture files",
    ),
    output_dir: Path = typer.Option(
        Path("instr"),
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

    test_cases = input.iterdir() if input.is_dir() else [input]
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
        Path("corpus8"),
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
        Path(os.getenv("SOLFUZZ_TARGET", "impl/lib/libsolfuzz_agave_v2.0.so")),
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
        Path("test_fixtures"),
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
    print("Creating fixtures...")
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
        Path("corpus8"),
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
        Path(os.getenv("SOLFUZZ_TARGET", "impl/lib/libsolfuzz_agave_v2.0.so")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path(os.getenv("FIREDANCER_TARGET", "impl/lib/libsolfuzz_firedancer.so"))],
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
        10000, "--chunk-size", "-c", help="Number of test results per file"
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
        help="Only fail on consensus failures. One such effect is to normalize error codes when comparing results",
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
    globals.default_harness_ctx = HARNESS_MAP[default_harness_ctx]

    # Set diff mode to consensus if specified
    globals.consensus_mode = consensus_mode

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

    # Make failed protobuf directory
    if save_failures:
        failed_protobufs_dir = globals.output_dir / "failed_protobufs"
        failed_protobufs_dir.mkdir(parents=True, exist_ok=True)

    test_cases = list(input.iterdir()) if input.is_dir() else [input]
    num_test_cases = len(test_cases)

    # Process the test results in parallel
    print("Running tests...")
    test_case_results = []
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

    print("Logging results...")
    passed = 0
    failed = 0
    skipped = 0
    failed_tests = []
    skipped_tests = []
    target_log_files = {target: None for target in shared_libraries}
    for file_stem, status, stringified_results in test_case_results:
        if stringified_results is None:
            skipped += 1
            skipped_tests.append(file_stem)
            continue

        for target, string_result in stringified_results.items():
            if (passed + failed) % log_chunk_size == 0:
                if target_log_files[target]:
                    target_log_files[target].close()
                target_log_files[target] = open(
                    globals.output_dir / target.stem / (file_stem + ".txt"), "w"
                )

            if not failures_only or status == -1:
                target_log_files[target].write(
                    file_stem
                    + ":\n"
                    + string_result
                    + "\n"
                    + "-" * LOG_FILE_SEPARATOR_LENGTH
                    + "\n"
                )

        if status == 1:
            passed += 1
        elif status == -1:
            failed += 1
            failed_tests.append(file_stem)
            if save_failures:
                failed_protobufs = list(input.glob(f"{file_stem}*"))
                for failed_protobuf in failed_protobufs:
                    shutil.copy(failed_protobuf, failed_protobufs_dir)

    print("Cleaning up...")
    for target in shared_libraries:
        if target_log_files[target]:
            target_log_files[target].close()
        globals.target_libraries[target].sol_compat_fini()

    peak_memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Peak Memory Usage: {peak_memory_usage_kb / 1024} MB")

    print(f"Total test cases: {passed + failed + skipped}")
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
    if verbose:
        print(f"Failed tests: {failed_tests}")
        print(f"Skipped tests: {skipped_tests}")
    if failed != 0 and save_failures:
        print("Failures tests are in: ", globals.output_dir / "failed_protobufs")


@app.command(help=f"Convert Context and/or Fixture messages to human-readable format.")
def decode_protobufs(
    input: Path = typer.Option(
        Path("raw_context"),
        "--input",
        "-i",
        help=f"Input protobuf file or directory of protobuf files",
    ),
    output_dir: Path = typer.Option(
        Path("readable_context"),
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
        Path(os.getenv("SOLFUZZ_TARGET", "impl/lib/libsolfuzz_agave_v2.0.so")),
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
        [Path(os.getenv("FIREDANCER_TARGET", "impl/lib/libsolfuzz_firedancer.so"))],
        "--target",
        "-t",
        help="Shared object (.so) target file paths (pairs with --keep-passing)."
        f" Targets must have required function entrypoints defined",
    ),
    output_dir: Path = typer.Option(
        Path("debug_mismatch"),
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
        "-s",
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
):
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

    curl_command = f"curl {fuzzcorp_url} --cookie s={fuzzcorp_cookie}"
    result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
    page_content = result.stdout
    soup = BeautifulSoup(page_content, "html.parser")
    for section_name in section_names_list:
        section_anchor = soup.find("a", {"name": f"lin_{section_name}"})

        if section_anchor:
            next_element = section_anchor.find_next_sibling()
            while next_element:
                if next_element.name == "table":
                    hrefs = [a["href"] for a in next_element.find_all("a", href=True)]
                    for href in hrefs:
                        repro_urls_list.append(urljoin(fuzzcorp_url, href))
                    break
                elif next_element.name == "p" and "No bugs found" in next_element.text:
                    print(f"No bugs found for section {section_name}.")
                    break
                elif next_element.name == "a" and next_element.has_attr("name"):
                    print(f"No table found in section {section_name}.")
                    break

                next_element = next_element.find_next_sibling()

            if not next_element:
                print(f"No relevant content found after section {section_name}.")
        else:
            print(f"Section {section_name} not found.")

    custom_data_urls = []
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
        custom_data_urls.append(custom_url)

    for url in custom_data_urls:
        zip_name = url.split("/")[-1]
        result = subprocess.run(
            ["wget", "-q", url, "-O", f"{globals.output_dir}/{zip_name}"],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            ["unzip", f"{globals.output_dir}/{zip_name}", "-d", globals.output_dir],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            f"mv {globals.output_dir}/repro_custom/*.fix {globals.inputs_dir}",
            shell=True,
            capture_output=True,
            text=True,
        )

    run_tests(
        input=globals.inputs_dir,
        reference_shared_library=reference_shared_library,
        default_harness_ctx=default_harness_ctx,
        shared_libraries=shared_libraries,
        output_dir=globals.output_dir / "test_results",
        num_processes=4,
        randomize_output_buffer=False,
        log_chunk_size=10000,
        verbose=True,
        consensus_mode=False,
        failures_only=False,
        save_failures=True,
        log_level=log_level,
    )


@app.command(
    help=f"""
            Run tests on a set of targets with a list of FuzzCorp mismatch links.

            Note: each `.so` target filename must be unique.
            """
)
def debug_non_repros(
    reference_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "impl/lib/libsolfuzz_agave_v2.0.so")),
        "--solana-target",
        "-s",
        help="Solana (or ground truth) shared object (.so) target file path",
    ),
    shared_libraries: List[Path] = typer.Option(
        [Path(os.getenv("FIREDANCER_TARGET", "impl/lib/libsolfuzz_firedancer.so"))],
        "--target",
        "-t",
        help="Shared object (.so) target file paths (pairs with --keep-passing)."
        f" Targets must have required function entrypoints defined",
    ),
    output_dir: Path = typer.Option(
        Path("debug_mismatch"),
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
        "-s",
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
):
    fuzzcorp_cookie = os.getenv("FUZZCORP_COOKIE")
    repro_urls_list = repro_urls.split(",") if repro_urls else []
    section_names_list = section_names.split(",") if section_names else []

    curl_command = f"curl {fuzzcorp_url} --cookie s={fuzzcorp_cookie}"
    result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
    page_content = result.stdout
    soup = BeautifulSoup(page_content, "html.parser")
    section_anchor = soup.find("a", {"name": "nonrepro"})
    table = section_anchor.find_next("table")

    lineage_to_links = defaultdict(list)

    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        href = cells[0].find("a")["href"]
        lineage = cells[2].text.strip()
        # Add the href to the list corresponding to the lineage key
        lineage_to_links[lineage].append(href)

    for section in section_names_list:
        for link in lineage_to_links[section]:
            repro_urls_list.append(urljoin(fuzzcorp_url, link))

    non_repro_urls = []
    for url in repro_urls_list:
        curl_command = f"curl {url} --cookie s={fuzzcorp_cookie}"
        result = subprocess.run(
            curl_command, shell=True, capture_output=True, text=True
        )
        page_content = result.stdout
        soup = BeautifulSoup(page_content, "html.parser")
        non_repro = soup.find("a", text="⬇️ Download Test Case")["href"]
        non_repro_urls.append(non_repro)

    globals.output_dir = output_dir

    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    globals.inputs_dir = globals.output_dir / "inputs"

    if globals.inputs_dir.exists():
        shutil.rmtree(globals.inputs_dir)
    globals.inputs_dir.mkdir(parents=True, exist_ok=True)

    for url in non_repro_urls:
        file_name = url.split("/")[-1]
        result = subprocess.run(
            ["wget", "-q", url, "-O", f"{globals.output_dir}/{file_name}"],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            f"mv {globals.output_dir}/{file_name} {globals.inputs_dir}",
            shell=True,
            capture_output=True,
            text=True,
        )

    run_tests(
        input=globals.inputs_dir,
        reference_shared_library=reference_shared_library,
        shared_libraries=shared_libraries,
        output_dir=globals.output_dir / "test_results",
        num_processes=4,
        randomize_output_buffer=False,
        log_chunk_size=10000,
        verbose=True,
        consensus_mode=False,
        failures_only=False,
        save_failures=True,
        log_level=log_level,
    )


@app.command(
    help=f"""
        Regenerate Fixture messages by checking FeatureSet compatibility with the target shared library. 
    """
)
def regenerate_fixtures(
    input: Path = typer.Option(
        Path("corpus8"),
        "--input",
        "-i",
        help=f"Either a file or directory containing messages",
    ),
    shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "impl/lib/libsolfuzz_agave_v2.0.so")),
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    output_dir: Path = typer.Option(
        Path("regenerated_fixtures"),
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
    all_fixtures: bool = typer.Option(
        False,
        "--all-fixtures",
        "-a",
        help="Regenerate all fixtures, regardless of FeatureSet compatibility. Will apply minimum compatible features.",
    ),
    log_level: int = typer.Option(
        5,
        "--log-level",
        "-l",
        help="FD logging level",
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

    for file in test_cases:
        fixture = read_fixture(file)
        harness_ctx = ENTRYPOINT_HARNESS_MAP[fixture.metadata.fn_entrypoint]

        target_features = features_utils.get_sol_compat_features_t(lib)
        features_path = pb_utils.find_field_with_type(
            harness_ctx.context_type.DESCRIPTOR, context_pb.FeatureSet.DESCRIPTOR
        )

        # TODO: support multiple FeatureSet fields
        assert len(features_path) == 1, "Only one FeatureSet field is supported"
        features_path = features_path[0]

        features = pb_utils.access_nested_field_safe(fixture.input, features_path)
        feature_set = set(features.features) if features else set()

        regenerate = True
        if not all_fixtures:
            # Skip regeneration if the features are already compatible with the target
            if features_utils.is_featureset_compatible(target_features, feature_set):
                regenerate = False

        if regenerate:
            num_regenerated += 1
            if dry_run:
                print(f"Would regenerate {file}")
            else:
                print(f"Regenerating {file}")
                # Apply minimum compatible features
                if features is not None:
                    features.features[:] = features_utils.min_compatible_featureset(
                        target_features, feature_set
                    )
                regenerated_fixture = create_fixture_from_context(
                    harness_ctx, fixture.input
                )
                write_fixture_to_disk(
                    harness_ctx,
                    file.stem,
                    regenerated_fixture.SerializeToString(),
                )

    lib.sol_compat_fini()
    print(f"Regenerated {num_regenerated} fixtures")


@app.command(
    help=f"""
        Regenerate all fixtures in provided test-vectors folder
    """
)
def regenerate_all_fixtures(
    test_vectors: Path = typer.Option(
        Path("corpus8"),
        "--input",
        "-i",
        help=f"Input test-vectors directory",
    ),
    output_dir: Path = typer.Option(
        Path("/tmp/regenerated_fixtures"),
        "--output-dir",
        "-o",
        help="Output directory for regenerated fixtures",
    ),
    shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_TARGET", "impl/lib/libsolfuzz_agave_v2.0.so")),
        "--target",
        "-t",
        help="Shared object (.so) target file path to execute",
    ),
    stubbed_shared_library: Path = typer.Option(
        Path(os.getenv("SOLFUZZ_STUBBED_TARGET", "impl/lib/libsolfuzz_firedancer.so")),
        "--stubbed-target",
        "-s",
        help="Stubbed shared object (.so) target file path to execute",
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
        if folder_harness_type in ["CpiHarness"]:
            regenerate_fixtures(
                input=Path(source_folder),
                shared_library=stubbed_shared_library,
                output_dir=Path(output_folder),
                dry_run=False,
                all_fixtures=True,
            )
        elif folder_harness_type in ["ElfLoaderHarness"]:
            shutil.copytree(source_folder, output_folder, dirs_exist_ok=True)
        else:
            regenerate_fixtures(
                input=Path(source_folder),
                shared_library=shared_library,
                output_dir=Path(output_folder),
                dry_run=False,
                all_fixtures=True,
            )

    print(f"Regenerated fixtures from {test_vectors} to {output_dir}")


if __name__ == "__main__":
    app()
