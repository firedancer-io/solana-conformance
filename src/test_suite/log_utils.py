import shutil
from typing import List
from test_suite.constants import LOG_FILE_SEPARATOR_LENGTH
import test_suite.globals as globals


def log_results(
    test_case_results,
    shared_libraries,
    log_chunk_size: int,
    failures_only: bool,
    save_failures: bool,
    save_successes: bool,
):
    # Make failed protobuf directory
    if save_failures:
        failed_protobufs_dir = globals.output_dir / "failed_protobufs"
        failed_protobufs_dir.mkdir(parents=True, exist_ok=True)
    if save_successes:
        successful_protobufs_dir = globals.output_dir / "successful_protobufs"
        successful_protobufs_dir.mkdir(parents=True, exist_ok=True)

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
            if save_successes:
                successful_protobufs = list(input.glob(f"{file_stem}*"))
                for successful_protobuf in successful_protobufs:
                    shutil.copy(successful_protobuf, successful_protobufs_dir)
        elif status == -1:
            failed += 1
            failed_tests.append(file_stem)
            if save_failures:
                failed_protobufs = list(input.glob(f"{file_stem}*"))
                for failed_protobuf in failed_protobufs:
                    shutil.copy(failed_protobuf, failed_protobufs_dir)

    for target in shared_libraries:
        if target_log_files[target]:
            target_log_files[target].close()

    return passed, failed, skipped, target_log_files, failed_tests, skipped_tests
