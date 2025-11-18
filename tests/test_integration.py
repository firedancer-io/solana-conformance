"""
Integration tests for solana-conformance CLI commands.

These tests verify that the major commands work correctly with both
single-threaded and multiprocessing execution modes.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.requires_targets
def test_execute_command(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test the execute command with a fixture file."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    fixture_file = next(sample_fixtures_dir.glob("*.fix"))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "execute",
            "-i",
            str(fixture_file),
            "-t",
            str(solfuzz_target),
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "No" not in result.stdout or "returned" in result.stdout


@pytest.mark.integration
@pytest.mark.requires_targets
def test_create_fixtures(
    solfuzz_target: Path,
    sample_contexts_dir: Path,
    temp_output_dir: Path,
    num_processes: int,
):
    """Test creating fixtures from contexts."""
    if not sample_contexts_dir.exists() or not list(
        sample_contexts_dir.glob("*.blockctx")
    ):
        pytest.skip("No sample contexts available")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "create-fixtures",
            "-i",
            str(sample_contexts_dir),
            "-s",
            str(solfuzz_target),
            "-o",
            str(temp_output_dir),
            "-h",
            "BlockHarness",  # Our sample contexts are block contexts
            "-p",
            str(num_processes),
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "files successfully written" in result.stdout

    # Verify fixtures were created
    fixtures = list(temp_output_dir.glob("*.fix"))
    assert len(fixtures) > 0, "No fixtures were created"


@pytest.mark.integration
@pytest.mark.requires_targets
def test_run_tests(
    solfuzz_target: Path,
    firedancer_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
    num_processes: int,
):
    """Test running tests on fixtures."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "run-tests",
            "-i",
            str(sample_fixtures_dir),
            "-s",
            str(solfuzz_target),
            "-t",
            str(firedancer_target),
            "-o",
            str(temp_output_dir),
            "-p",
            str(num_processes),
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in [0, 1], f"Command failed unexpectedly: {result.stderr}"
    assert "Total test cases:" in result.stdout
    assert "Passed:" in result.stdout


@pytest.mark.integration
@pytest.mark.requires_targets
def test_exec_fixtures(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
    num_processes: int,
):
    """Test executing fixtures and verifying effects."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "exec-fixtures",
            "-i",
            str(sample_fixtures_dir),
            "-t",
            str(solfuzz_target),
            "-o",
            str(temp_output_dir),
            "-p",
            str(num_processes),
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in [0, 1], f"Command failed unexpectedly: {result.stderr}"
    assert "Total test cases:" in result.stdout


@pytest.mark.integration
@pytest.mark.requires_targets
def test_regenerate_fixtures(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
    num_processes: int,
):
    """Test regenerating fixtures with feature changes."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "regenerate-fixtures",
            "-i",
            str(sample_fixtures_dir),
            "-t",
            str(solfuzz_target),
            "-o",
            str(temp_output_dir),
            "-p",
            str(num_processes),
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Regenerated" in result.stdout

    # Verify fixtures were regenerated
    fixtures = list(temp_output_dir.glob("*.fix"))
    assert len(fixtures) > 0, "No fixtures were regenerated"


@pytest.mark.integration
def test_decode_protobufs(
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
    num_processes: int,
):
    """Test decoding protobufs to human-readable format."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "decode-protobufs",
            "-i",
            str(sample_fixtures_dir),
            "-o",
            str(temp_output_dir),
            "-p",
            str(num_processes),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "files successfully written" in result.stdout

    # Verify decoded files were created
    txt_files = list(temp_output_dir.glob("*.txt"))
    assert len(txt_files) > 0, "No decoded files were created"


@pytest.mark.integration
def test_fix_to_ctx(
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
    num_processes: int,
):
    """Test extracting contexts from fixtures."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "fix-to-ctx",
            "-i",
            str(sample_fixtures_dir),
            "-o",
            str(temp_output_dir),
            "-p",
            str(num_processes),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "files successfully written" in result.stdout

    # Verify context files were created
    bin_files = list(temp_output_dir.glob("*.bin"))
    assert len(bin_files) > 0, "No context files were created"


@pytest.mark.integration
@pytest.mark.requires_targets
def test_debug_mode_vs_parallel(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test that debug mode and parallel mode produce consistent results."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    # Run in debug mode
    debug_output = temp_output_dir / "debug"
    result_debug = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "regenerate-fixtures",
            "-i",
            str(sample_fixtures_dir),
            "-t",
            str(solfuzz_target),
            "-o",
            str(debug_output),
            "--debug-mode",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    # Run in parallel mode
    parallel_output = temp_output_dir / "parallel"
    result_parallel = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "regenerate-fixtures",
            "-i",
            str(sample_fixtures_dir),
            "-t",
            str(solfuzz_target),
            "-o",
            str(parallel_output),
            "-p",
            "4",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result_debug.returncode == 0, f"Debug mode failed: {result_debug.stderr}"
    assert (
        result_parallel.returncode == 0
    ), f"Parallel mode failed: {result_parallel.stderr}"

    # Verify same number of fixtures were created
    debug_fixtures = list(debug_output.glob("*.fix"))
    parallel_fixtures = list(parallel_output.glob("*.fix"))

    assert len(debug_fixtures) == len(
        parallel_fixtures
    ), f"Different number of fixtures: debug={len(debug_fixtures)}, parallel={len(parallel_fixtures)}"


@pytest.mark.integration
@pytest.mark.requires_targets
def test_process_count_handling(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test that requesting more processes than items doesn't cause issues."""
    if not sample_fixtures_dir.exists():
        pytest.skip("No sample fixtures available")

    # Get a small number of fixtures (e.g., 2)
    fixtures = list(sample_fixtures_dir.glob("*.fix"))[:2]
    if len(fixtures) < 2:
        pytest.skip("Need at least 2 fixtures for this test")

    # Create temp dir with just these fixtures
    small_input_dir = temp_output_dir / "small_input"
    small_input_dir.mkdir(parents=True, exist_ok=True)
    for fixture in fixtures:
        shutil.copy(fixture, small_input_dir)

    # Request 16 processes for 2 items (should cap at 2)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "regenerate-fixtures",
            "-i",
            str(small_input_dir),
            "-t",
            str(solfuzz_target),
            "-o",
            str(temp_output_dir / "output"),
            "-p",
            "16",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert (
        result.returncode == 0
    ), f"Command failed with too many processes: {result.stderr}"
    assert "Regenerated" in result.stdout
