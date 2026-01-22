"""
Tests for shell scripts and dependency management.

These tests verify that the build scripts work correctly.
"""

import subprocess
import os
from pathlib import Path

import pytest


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def run_script(script: str, *args, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell script from the project root."""
    cmd = [str(PROJECT_ROOT / script)] + list(args)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


class TestDepsScript:
    """Tests for deps.sh script."""

    def test_deps_help(self):
        """Test deps.sh --help shows usage."""
        result = run_script("deps.sh", "--help")
        assert result.returncode == 0
        assert "Usage" in result.stdout
        assert "flatc" in result.stdout
        assert "buf" in result.stdout

    def test_deps_status(self):
        """Test deps.sh --status shows dependency status."""
        result = run_script("deps.sh", "--status")
        assert result.returncode == 0
        assert "Dependency Status" in result.stdout
        assert "flatbuffers" in result.stdout.lower()
        assert "protosol" in result.stdout.lower()

    def test_deps_invalid_command(self):
        """Test deps.sh with invalid command shows error."""
        result = run_script("deps.sh", "invalid_command", check=False)
        assert result.returncode != 0
        assert "Unknown command" in result.stdout or "ERROR" in result.stdout


class TestSubmodules:
    """Tests for git submodules."""

    def test_flatbuffers_submodule_exists(self):
        """Test that flatbuffers submodule is configured."""
        submodule_path = PROJECT_ROOT / "shlr" / "flatbuffers"
        assert submodule_path.exists(), "flatbuffers submodule directory missing"
        assert (
            submodule_path / "CMakeLists.txt"
        ).exists(), "flatbuffers not initialized"

    def test_protosol_submodule_exists(self):
        """Test that protosol submodule is configured."""
        submodule_path = PROJECT_ROOT / "shlr" / "protosol"
        assert submodule_path.exists(), "protosol submodule directory missing"
        assert (submodule_path / "proto").exists(), "protosol not initialized"

    def test_protosol_has_schemas(self):
        """Test that protosol has required schema files."""
        proto_dir = PROJECT_ROOT / "shlr" / "protosol" / "proto"
        fbs_dir = PROJECT_ROOT / "shlr" / "protosol" / "flatbuffers"

        if proto_dir.exists():
            proto_files = list(proto_dir.glob("*.proto"))
            assert len(proto_files) > 0, "No .proto files found"

        if fbs_dir.exists():
            fbs_files = list(fbs_dir.glob("*.fbs"))
            assert len(fbs_files) > 0, "No .fbs files found"


class TestVendoredTools:
    """Tests for vendored tools (when installed)."""

    @pytest.fixture
    def flatc_path(self):
        """Path to vendored flatc."""
        return PROJECT_ROOT / "opt" / "bin" / "flatc"

    @pytest.fixture
    def buf_path(self):
        """Path to vendored buf."""
        return PROJECT_ROOT / "opt" / "bin" / "buf"

    def test_flatc_works(self, flatc_path):
        """Test that vendored flatc works (if installed)."""
        if not flatc_path.exists():
            pytest.skip("flatc not installed (run deps.sh first)")

        result = subprocess.run(
            [str(flatc_path), "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "flatc" in result.stdout.lower()

    def test_buf_works(self, buf_path):
        """Test that vendored buf works (if installed)."""
        if not buf_path.exists():
            pytest.skip("buf not installed (run deps.sh first)")

        result = subprocess.run(
            [str(buf_path), "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestGeneratedCode:
    """Tests for generated code (when available)."""

    def test_protobuf_bindings_exist(self):
        """Test that protobuf bindings are generated."""
        protos_dir = PROJECT_ROOT / "src" / "test_suite" / "protos"
        if not protos_dir.exists():
            pytest.skip("Protobuf bindings not generated (run fetch_and_generate.sh)")

        pb2_files = list(protos_dir.glob("*_pb2.py"))
        assert len(pb2_files) > 0, "No *_pb2.py files found"

    def test_flatbuffers_bindings_exist(self):
        """Test that FlatBuffers bindings are generated."""
        fbs_dir = PROJECT_ROOT / "src" / "test_suite" / "flatbuffers"
        if not fbs_dir.exists():
            pytest.skip(
                "FlatBuffers bindings not generated (run fetch_and_generate.sh)"
            )

        # Check for the org.solana.sealevel.v2 package structure
        v2_dir = fbs_dir / "org" / "solana" / "sealevel" / "v2"
        assert v2_dir.exists(), "FlatBuffers v2 package not found"

        py_files = list(v2_dir.glob("*.py"))
        assert len(py_files) > 0, "No Python files in FlatBuffers package"
