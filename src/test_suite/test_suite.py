import shutil
from typing import List
import typer
from collections import defaultdict
import ctypes
from multiprocessing import Pool
from pathlib import Path
import subprocess
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
from test_suite.fixture_utils import (
    create_fixture,
    extract_context_from_fixture,
)
from test_suite.multiprocessing_utils import (
    decode_single_test_case,
    read_context,
    initialize_process_output_buffers,
    process_target,
    run_test,
    serialize_context,
)
import test_suite.globals as globals
from test_suite.debugger import debug_host
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
harness_type = os.getenv("HARNESS_TYPE")
if harness_type:
    globals.harness_ctx = eval(harness_type)
else:
    globals.harness_ctx = InstrHarness
    harness_type = "InstrHarness"

app = typer.Typer(
    help=f"Validate effects from clients using {globals.harness_ctx.context_type.__name__} Protobuf messages."
)


@app.command(
    help=f"Execute {globals.harness_ctx.context_type.__name__} message(s) and print the effects."
)
def exec_instr(
    file_or_dir: Path = typer.Option(
        None,
        "--input",
        "-i",
        help=f"Input {globals.harness_ctx.context_type.__name__} file or directory of files",
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
):
    # Initialize output buffers and shared library
    initialize_process_output_buffers(randomize_output_buffer=randomize_output_buffer)
    try:
        lib = ctypes.CDLL(shared_library)
    except:
        set_ld_preload_asan()
    lib.sol_compat_init()

    files_to_exec = file_or_dir.iterdir() if file_or_dir.is_dir() else [file_or_dir]
    for file in files_to_exec:
        print(f"Handling {file}...")

        # Execute and cleanup
        context = serialize_context(file)
        start = time.time()
        effects = process_target(lib, context)
        end = time.time()

        print(f"Total time taken for {file}: {(end - start) * 1000} ms\n------------")

        if not effects:
            print(f"No {globals.harness_ctx.effects_type.__name__} returned")
            continue

        serialized_effects = effects.SerializeToString(deterministic=True)

        # Prune execution results
        serialized_effects = globals.harness_ctx.prune_effects_fn(
            context,
            {shared_library: serialized_effects},
        )[shared_library]

        parsed_instruction_effects = globals.harness_ctx.effects_type()
        parsed_instruction_effects.ParseFromString(serialized_effects)

        # Print human-readable output
        if parsed_instruction_effects:
            globals.harness_ctx.effects_human_encode_fn(parsed_instruction_effects)

        print(parsed_instruction_effects)

    lib.sol_compat_fini()


@app.command()
def debug_instr(
    file: Path = typer.Option(None, "--input", "-i", help="Input file"),
    shared_library: Path = typer.Option(
        Path("impl/lib/libsolfuzz_firedancer.so"),
        "--target",
        "-t",
        help="Shared object (.so) target file path to debug",
    ),
    debugger: str = typer.Option(
        "gdb", "--debugger", "-d", help="Debugger to use (gdb, rust-gdb)"
    ),
):
    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"Processing {file.name}...")

    # Decode the file and pass it into GDB
    instruction_context = read_context(file)
    assert instruction_context is not None, f"Unable to read {file.name}"
    debug_host(shared_library, instruction_context, gdb=debugger)


@app.command(
    help=f"Extract {globals.harness_ctx.context_type.__name__} messages from fixtures."
)
def instr_from_fixtures(
    input_dir: Path = typer.Option(
        Path("fixtures"),
        "--input-dir",
        "-i",
        help=f"Input directory containing {globals.harness_ctx.fixture_type.__name__} messages",
    ),
    output_dir: Path = typer.Option(
        Path("instr"),
        "--output-dir",
        "-o",
        help=f"Output directory for {globals.harness_ctx.context_type.__name__} messages",
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

    test_cases = list(input_dir.iterdir())
    num_test_cases = len(test_cases)

    print(f"Converting to {globals.harness_ctx.context_type.__name__}...")
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
             Create test fixtures from a directory of {globals.harness_ctx.context_type.__name__} messages.
             Effects are generated by the target passed in with --solana-target or -s. 
             You can also pass in additional targets with --target or -t 
             and use --keep-passing or -k to only generate effects for test cases that match.
             """
)
def create_fixtures(
    input_path: Path = typer.Option(
        Path("corpus8"),
        "--input-dir",
        "-i",
        help=f"Either a file or directory containing {globals.harness_ctx.context_type.__name__} messages",
    ),
    solana_shared_library: Path = typer.Option(
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
        f" Targets must have {globals.harness_ctx.fuzz_fn_name} defined",
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
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library
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
        lib.sol_compat_init()
        globals.target_libraries[target] = lib

    test_cases = [input_path] if input_path.is_file() else list(input_path.iterdir())
    num_test_cases = len(test_cases)

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
            Run tests on a set of targets with a directory of {globals.harness_ctx.context_type.__name__} 
            or {globals.harness_ctx.fixture_type.__name__} messages.

            Note: each `.so` target filename must be unique.
            """
)
def run_tests(
    file_or_dir: Path = typer.Option(
        Path("corpus8"),
        "--input",
        "-i",
        help=f"Single input file or input directory containing {globals.harness_ctx.context_type.__name__}"
        f" or { globals.harness_ctx.fixture_type.__name__ } messages",
    ),
    solana_shared_library: Path = typer.Option(
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
):
    # Add Solana library to shared libraries
    shared_libraries = [solana_shared_library] + shared_libraries

    # Specify globals
    globals.output_dir = output_dir
    globals.solana_shared_library = solana_shared_library

    # Set diff mode to consensus if specified
    if consensus_mode:
        globals.harness_ctx.diff_effect_fn = (
            globals.harness_ctx.consensus_diff_effect_fn
        )

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize shared libraries
    for target in shared_libraries:
        # Load in and initialize shared libraries
        lib = ctypes.CDLL(target)
        lib.sol_compat_init()
        globals.target_libraries[target] = lib

        # Make log output directories for each shared library
        log_dir = globals.output_dir / target.stem
        log_dir.mkdir(parents=True, exist_ok=True)

    # Make failed protobuf directory
    if save_failures:
        failed_protobufs_dir = globals.output_dir / "failed_protobufs"
        failed_protobufs_dir.mkdir(parents=True, exist_ok=True)

    test_cases = list(file_or_dir.iterdir()) if file_or_dir.is_dir() else [file_or_dir]
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
                failed_protobufs = list(file_or_dir.glob(f"{file_stem}*"))
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


@app.command(
    help=f"Convert {globals.harness_ctx.context_type.__name__} messages to human-readable format."
)
def decode_protobuf(
    input_path: Path = typer.Option(
        Path("raw_context"),
        "--input",
        "-i",
        help=f"Either a {globals.harness_ctx.context_type.__name__} message or directory of messages",
    ),
    output_dir: Path = typer.Option(
        Path("readable_context"),
        "--output-dir",
        "-o",
        help=f"Output directory for base58-encoded, human-readable {globals.harness_ctx.context_type.__name__} messages",
    ),
    num_processes: int = typer.Option(
        4, "--num-processes", "-p", help="Number of processes to use"
    ),
):
    globals.output_dir = output_dir

    # Create the output directory, if necessary
    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.is_dir():
        ok = decode_single_test_case(input_path)
        if not ok:
            print(f"Error decoding {input_path}")
        return

    num_test_cases = len(list(input_path.iterdir()))

    write_results = []
    with Pool(processes=num_processes) as pool:
        for result in tqdm.tqdm(
            pool.imap(decode_single_test_case, input_path.iterdir()),
            total=num_test_cases,
        ):
            write_results.append(result)

    print("-" * LOG_FILE_SEPARATOR_LENGTH)
    print(f"{len(write_results)} total files seen")
    print(f"{sum(write_results)} files successfully written")


@app.command(help=f"List harness types available for use.")
def list_harness_types():
    # pretty print harness types
    print(f"Currently set harness type: {harness_type}\n")

    print("Available harness types:")
    for name in HARNESS_LIST:
        print(f"- {name}")
    print("\nTo use, export the harness type to HARNESS_TYPE env var. Example:")
    print(f"export HARNESS_TYPE={HARNESS_LIST[0]}")


@app.command(
    help=f"""
            Run tests on a set of targets with a list of FuzzCorp mismatch links.

            Note: each `.so` target filename must be unique.
            """
)
def debug_mismatches(
    solana_shared_library: Path = typer.Option(
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
        f" Targets must have {globals.harness_ctx.fuzz_fn_name} defined",
    ),
    output_dir: Path = typer.Option(
        Path("debug_mismatch"),
        "--output-dir",
        "-o",
        help=f"Output directory for {globals.harness_ctx.context_type.__name__} messages",
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
        os.getenv("FUZZCORP_URL", ""),
        "--fuzzcorp-url",
        "-f",
        help="Comma-delimited list of FuzzCorp section names",
    ),
):
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

    globals.output_dir = output_dir

    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    globals.inputs_dir = globals.output_dir / "inputs"

    if globals.inputs_dir.exists():
        shutil.rmtree(globals.inputs_dir)
    globals.inputs_dir.mkdir(parents=True, exist_ok=True)

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
            f"mv {globals.output_dir}/repro_custom/*ctx {globals.inputs_dir}",
            shell=True,
            capture_output=True,
            text=True,
        )

    run_tests(
        file_or_dir=globals.inputs_dir,
        solana_shared_library=solana_shared_library,
        shared_libraries=shared_libraries,
        output_dir=globals.output_dir / "test_results",
        num_processes=4,
        randomize_output_buffer=False,
        log_chunk_size=10000,
        verbose=True,
        consensus_mode=False,
        failures_only=False,
        save_failures=True,
    )


@app.command(
    help=f"""
            Run tests on a set of targets with a list of FuzzCorp mismatch links.

            Note: each `.so` target filename must be unique.
            """
)
def debug_non_repros(
    solana_shared_library: Path = typer.Option(
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
        f" Targets must have {globals.harness_ctx.fuzz_fn_name} defined",
    ),
    output_dir: Path = typer.Option(
        Path("debug_mismatch"),
        "--output-dir",
        "-o",
        help=f"Output directory for {globals.harness_ctx.context_type.__name__} messages",
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
        os.getenv("FUZZCORP_URL", ""),
        "--fuzzcorp-url",
        "-f",
        help="Comma-delimited list of FuzzCorp section names",
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

        import pdb

        pdb.set_trace

    run_tests(
        file_or_dir=globals.inputs_dir,
        solana_shared_library=solana_shared_library,
        shared_libraries=shared_libraries,
        output_dir=globals.output_dir / "test_results",
        num_processes=4,
        randomize_output_buffer=False,
        log_chunk_size=10000,
        verbose=True,
        consensus_mode=False,
        failures_only=False,
        save_failures=True,
    )


@app.command(
    help=f"""
        Regenerate {globals.harness_ctx.fixture_type.__name__} messages by
        checking FeatureSet compatibility with the target shared library. 
    """
)
def regenerate_fixtures(
    input_path: Path = typer.Option(
        Path("corpus8"),
        "--input-dir",
        "-i",
        help=f"Either a file or directory containing {globals.harness_ctx.fixture_type.__name__} messages",
    ),
    shared_library: Path = typer.Option(
        Path(os.getenv("FIREDANCER_TARGET", "impl/lib/libsolfuzz_firedancer.so")),
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
):
    globals.output_dir = output_dir
    globals.reference_shared_library = shared_library

    if globals.output_dir.exists():
        shutil.rmtree(globals.output_dir)
    globals.output_dir.mkdir(parents=True, exist_ok=True)

    lib: ctypes.CDLL = ctypes.CDLL(shared_library)
    lib.sol_compat_init()
    globals.target_libraries[shared_library] = lib

    target_features = features_utils.get_sol_compat_features_t(lib)
    features_path = pb_utils.find_field_with_type(
        globals.harness_ctx.context_type.DESCRIPTOR, context_pb.FeatureSet.DESCRIPTOR
    )

    # TODO: support multiple FeatureSet fields
    assert len(features_path) == 1, "Only one FeatureSet field is supported"
    features_path = features_path[0]

    test_cases = list(input_path.iterdir()) if input_path.is_dir() else [input_path]

    needs_regeneration = []

    for file in test_cases:
        fixture = globals.harness_ctx.fixture_type()
        with open(file, "rb") as f:
            fixture.ParseFromString(f.read())

        features = pb_utils.access_nested_field_safe(fixture.input, features_path)
        feature_set = set(features.features)

        if not feature_set:
            print(f"FeatureSet not found in {file}, marking for regeneration")
            needs_regeneration.append(file)
            continue
        if not features_utils.is_featureset_compatible(target_features, feature_set):
            print(
                f"{file} FeatureSet incompatible with target, marking for regeneration"
            )
            needs_regeneration.append(file)

    pass


if __name__ == "__main__":
    app()
