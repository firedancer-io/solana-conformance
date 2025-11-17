"""
Pytest configuration and fixtures for solana-conformance integration tests.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def solfuzz_target() -> Path:
    """Get the solfuzz-agave target .so file."""
    # Try local test targets directory first (checked into git)
    local_target = Path(__file__).parent / "targets" / "libsolfuzz_agave.so"
    if local_target.exists():
        return local_target

    # Fallback to environment variable
    target = os.getenv("SOLFUZZ_TARGET")
    if target and Path(target).exists():
        return Path(target)

    pytest.skip(
        "solfuzz-agave target not found. "
        "Either place libsolfuzz_agave.so in tests/targets/ or set SOLFUZZ_TARGET environment variable."
    )


@pytest.fixture(scope="session")
def firedancer_target() -> Path:
    """Get the firedancer target .so file."""
    # Try local test targets directory first (checked into git)
    local_target = Path(__file__).parent / "targets" / "libfd_exec_sol_compat.so"
    if local_target.exists():
        return local_target

    # Fallback to environment variable
    target = os.getenv("FIREDANCER_TARGET")
    if target and Path(target).exists():
        return Path(target)

    pytest.skip(
        "firedancer target not found. "
        "Either place libfd_exec_sol_compat.so in tests/targets/ or set FIREDANCER_TARGET environment variable."
    )


@pytest.fixture
def temp_output_dir() -> Iterator[Path]:
    """Create a temporary directory for test outputs."""
    temp_dir = Path(tempfile.mkdtemp(prefix="solana_conformance_test_"))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_fixtures_dir(test_data_dir: Path) -> Path:
    """Return path to sample fixtures directory."""
    return test_data_dir / "fixtures"


@pytest.fixture
def sample_contexts_dir(test_data_dir: Path) -> Path:
    """Return path to sample contexts directory."""
    return test_data_dir / "contexts"


@pytest.fixture(params=[1, 4], ids=["single-threaded", "multiprocessing"])
def num_processes(request) -> int:
    """Parametrize tests to run with both single-threaded and multiprocessing."""
    return request.param


@pytest.fixture(params=[False, True], ids=["normal", "debug"])
def debug_mode(request) -> bool:
    """Parametrize tests to run with both normal and debug modes."""
    return request.param
