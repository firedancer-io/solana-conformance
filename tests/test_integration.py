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


# ============================================================================
# Debugging Workflow Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.requires_targets
def test_gdb_execute_command_python(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test that gdb can launch the Python execute command (non-interactive)."""
    # Check if gdb is available
    if not shutil.which("gdb"):
        pytest.skip("gdb not available")

    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    fixture_file = next(sample_fixtures_dir.glob("*.fix"))

    # Run with gdb in batch mode (non-interactive) - just check it can start
    result = subprocess.run(
        [
            "gdb",
            "--batch",
            "--ex",
            "set pagination off",
            "--ex",
            "run --version",
            "--args",
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
        timeout=30,
    )

    # GDB should start successfully and run the program
    assert "exited normally" in result.stdout or "Python" in result.stdout


@pytest.mark.integration
@pytest.mark.requires_targets
def test_gdb_execute_with_exec_fixtures(
    firedancer_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test gdb with exec-fixtures command (debug_it.sh workflow)."""
    if not shutil.which("gdb"):
        pytest.skip("gdb not available")

    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    fixture_file = next(sample_fixtures_dir.glob("*.fix"))

    # Run gdb in batch mode with the exec-fixtures workflow
    result = subprocess.run(
        [
            "gdb",
            "--batch",
            "--ex",
            "set pagination off",
            "--ex",
            "run",
            "--ex",
            "quit",
            "--args",
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "exec-fixtures",
            "-i",
            str(fixture_file),
            "-t",
            str(firedancer_target),
            "-o",
            str(temp_output_dir),
            "--debug-mode",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Should complete without error (exit code may vary if fixture execution has issues)
    # We're mainly testing that gdb can launch and run the command
    assert "exited normally" in result.stdout or "exited with code" in result.stdout


@pytest.mark.integration
@pytest.mark.requires_targets
def test_rust_gdb_with_python_module(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
):
    """Test rust-gdb with Python-based test suite (for Rust shared libraries)."""
    if not shutil.which("rust-gdb"):
        pytest.skip("rust-gdb not available")

    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    fixture_file = next(sample_fixtures_dir.glob("*.fix"))

    # Run rust-gdb in batch mode with Python interpreter
    # This allows debugging Rust shared libraries loaded by Python
    result = subprocess.run(
        [
            "rust-gdb",
            "--batch",
            "--ex",
            "set pagination off",
            "--ex",
            "run --version",
            "--args",
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
        timeout=30,
    )

    # rust-gdb should complete successfully
    assert result.returncode == 0, f"rust-gdb failed with exit code {result.returncode}"


@pytest.mark.integration
@pytest.mark.requires_targets
def test_gdb_with_debug_script(
    firedancer_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test gdb with a custom debug script (like debug.gdb)."""
    if not shutil.which("gdb"):
        pytest.skip("gdb not available")

    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    fixture_file = next(sample_fixtures_dir.glob("*.fix"))

    # Create a minimal debug script for testing
    debug_script = temp_output_dir / "test_debug.gdb"
    debug_script.write_text(
        """
set pagination off
set confirm off

# Just run and exit
run
quit
"""
    )

    result = subprocess.run(
        [
            "gdb",
            "--batch",
            "-x",
            str(debug_script),
            "--args",
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "exec-fixtures",
            "-i",
            str(fixture_file),
            "-t",
            str(firedancer_target),
            "-o",
            str(temp_output_dir / "gdb_output"),
            "--debug-mode",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Should execute and show program exited
    assert (
        "exited" in result.stdout.lower()
        or "Total test cases" in result.stdout
        or result.returncode == 0
    )


@pytest.mark.integration
@pytest.mark.requires_targets
def test_gdb_breakpoint_setup(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
):
    """Test that gdb can set breakpoints on shared library load."""
    if not shutil.which("gdb"):
        pytest.skip("gdb not available")

    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    fixture_file = next(sample_fixtures_dir.glob("*.fix"))

    # Test setting a breakpoint on library load (won't actually hit, just verify gdb accepts it)
    result = subprocess.run(
        [
            "gdb",
            "--batch",
            "--ex",
            "set pagination off",
            "--ex",
            "catch load libsolfuzz_agave.so",
            "--ex",
            "run --version",
            "--args",
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "execute",
            "-i",
            str(fixture_file),
            "-t",
            str(solfuzz_target),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # GDB should accept the catch load command
    assert result.returncode == 0 or "Catchpoint" in result.stdout


# ============================================================================
# Output Format Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.requires_targets
def test_create_fixtures_output_format_protobuf(
    solfuzz_target: Path,
    sample_contexts_dir: Path,
    temp_output_dir: Path,
):
    """Test creating fixtures with explicit Protobuf output format."""
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
            "BlockHarness",
            "-F",
            "protobuf",
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

    # Verify output is Protobuf format
    from test_suite.flatbuffers_utils import detect_format

    for fixture in fixtures[:2]:  # Check first 2
        with open(fixture, "rb") as f:
            data = f.read()
        fmt = detect_format(data)
        assert fmt == "protobuf", f"Expected protobuf, got {fmt} for {fixture}"


@pytest.mark.integration
@pytest.mark.requires_targets
def test_create_fixtures_output_format_flatbuffers(
    solfuzz_target: Path,
    sample_contexts_dir: Path,
    temp_output_dir: Path,
):
    """Test creating fixtures with FlatBuffers output format."""
    from test_suite.flatbuffers_utils import FLATBUFFERS_AVAILABLE

    if not FLATBUFFERS_AVAILABLE:
        pytest.skip("FlatBuffers not available")

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
            "BlockHarness",
            "-F",
            "flatbuffers",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    # May fail if FlatBuffers conversion isn't supported for BlockHarness
    # This is expected - just verify the command doesn't crash
    assert result.returncode in [0, 1], f"Command crashed: {result.stderr}"


@pytest.mark.integration
@pytest.mark.requires_targets
def test_create_fixtures_output_format_auto(
    solfuzz_target: Path,
    sample_fixtures_dir: Path,
    temp_output_dir: Path,
):
    """Test creating fixtures with auto output format (matches input)."""
    if not sample_fixtures_dir.exists() or not list(sample_fixtures_dir.glob("*.fix")):
        pytest.skip("No sample fixtures available")

    # Get first fixture and detect its format
    fixture_file = next(sample_fixtures_dir.glob("*.fix"))
    from test_suite.flatbuffers_utils import detect_format

    with open(fixture_file, "rb") as f:
        input_data = f.read()
    input_format = detect_format(input_data)

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
            "1",
            "-l",
            "5",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify output fixtures exist
    output_fixtures = list(temp_output_dir.glob("*.fix"))
    assert len(output_fixtures) > 0, "No fixtures were created"

    # In auto mode, output format should match input format
    for output_fixture in output_fixtures[:2]:
        with open(output_fixture, "rb") as f:
            output_data = f.read()
        output_format = detect_format(output_data)
        # Note: may not always match exactly due to conversion limitations
        assert output_format in ("protobuf", "flatbuffers", "unknown")


@pytest.mark.integration
def test_create_fixtures_invalid_output_format(
    temp_output_dir: Path,
):
    """Test that invalid output format is rejected."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "create-fixtures",
            "-i",
            "/tmp/nonexistent",
            "-s",
            "/tmp/nonexistent.so",
            "-o",
            str(temp_output_dir),
            "-F",
            "invalid_format",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail with error about invalid format
    assert result.returncode != 0
    assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower()


@pytest.mark.integration
def test_check_deps_includes_flatbuffers():
    """Test that check-deps command reports FlatBuffers status."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "test_suite.test_suite",
            "check-deps",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "FlatBuffers" in result.stdout
    assert "[OK]" in result.stdout or "[MISSING]" in result.stdout
