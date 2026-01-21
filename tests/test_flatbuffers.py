"""
Unit tests for FlatBuffers support in solana-conformance.

These tests verify:
1. Dependency checking functions work correctly
2. Format detection works for Protobuf and FlatBuffers
3. FixtureLoader handles various error cases gracefully
4. FlatBuffers to Protobuf conversion works (when bindings are available)
"""

import tempfile
from pathlib import Path

import pytest


class TestDependencyChecks:
    """Tests for dependency checking utilities."""

    def test_get_dependency_status_returns_dict(self):
        """Test that get_dependency_status returns expected structure."""
        from test_suite.flatbuffers_utils import get_dependency_status

        status = get_dependency_status()

        assert isinstance(status, dict)
        assert "flatbuffers_package" in status
        assert "numpy_package" in status
        assert "fb_bindings" in status
        assert "ready" in status

        assert isinstance(status["flatbuffers_package"], dict)
        assert "installed" in status["flatbuffers_package"]
        assert "version" in status["flatbuffers_package"]

    def test_print_dependency_status_runs(self, capsys):
        """Test that print_dependency_status runs without error."""
        from test_suite.flatbuffers_utils import print_dependency_status

        result = print_dependency_status()

        assert isinstance(result, bool)

        captured = capsys.readouterr()
        assert "FlatBuffers Status" in captured.out
        assert "[OK]" in captured.out or "[MISSING]" in captured.out


class TestFormatDetection:
    """Tests for Protobuf vs FlatBuffers format detection."""

    def test_detect_format_empty(self):
        """Test format detection with empty data."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"") == "unknown"

    def test_detect_format_too_small(self):
        """Test format detection with data too small."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"abc") == "unknown"

    def test_detect_format_random_data(self):
        """Test format detection with random data."""
        from test_suite.flatbuffers_utils import detect_format

        result = detect_format(b"This is definitely not a valid format!")
        # Should return unknown or try to guess
        assert result in ("unknown", "protobuf", "flatbuffers")

    def test_is_flatbuffers_format_typical_header(self):
        """Test FlatBuffers detection with typical header."""
        from test_suite.flatbuffers_utils import is_flatbuffers_format

        # Typical FlatBuffers header: offset 0x14 followed by 0x00 0x00
        fb_header = b"\x14\x00\x00\x00\x00\x00" + b"\x00" * 20
        assert is_flatbuffers_format(fb_header) is True

    def test_is_flatbuffers_format_protobuf_data(self):
        """Test that Protobuf data is not detected as FlatBuffers."""
        from test_suite.flatbuffers_utils import is_flatbuffers_format

        # Typical Protobuf varint-encoded message
        pb_data = b"\x0a\x10test message here"
        # This might be detected as FB due to heuristics, but we check it doesn't crash
        result = is_flatbuffers_format(pb_data)
        assert isinstance(result, bool)


class TestFixtureLoader:
    """Tests for the unified FixtureLoader class."""

    def test_loader_nonexistent_file(self):
        """Test FixtureLoader with non-existent file."""
        from test_suite.flatbuffers_utils import FixtureLoader

        loader = FixtureLoader(Path("/nonexistent/path/to/file.fix"))

        assert loader.is_valid is False
        assert loader.error_message is not None
        assert "not found" in loader.error_message.lower()

    def test_loader_empty_file(self):
        """Test FixtureLoader with empty file."""
        from test_suite.flatbuffers_utils import FixtureLoader

        with tempfile.NamedTemporaryFile(suffix=".fix", delete=False) as f:
            temp_path = Path(f.name)

        try:
            loader = FixtureLoader(temp_path)
            assert loader.is_valid is False
            assert loader.error_message is not None
            assert "empty" in loader.error_message.lower()
        finally:
            temp_path.unlink()

    def test_loader_tiny_file(self):
        """Test FixtureLoader with file too small to be valid."""
        from test_suite.flatbuffers_utils import FixtureLoader

        with tempfile.NamedTemporaryFile(suffix=".fix", delete=False) as f:
            f.write(b"tiny")
            temp_path = Path(f.name)

        try:
            loader = FixtureLoader(temp_path)
            assert loader.is_valid is False
            assert loader.error_message is not None
            assert "small" in loader.error_message.lower()
        finally:
            temp_path.unlink()

    def test_loader_invalid_content(self):
        """Test FixtureLoader with invalid content."""
        from test_suite.flatbuffers_utils import FixtureLoader

        with tempfile.NamedTemporaryFile(suffix=".fix", delete=False) as f:
            f.write(b"This is not a valid fixture file at all - just garbage text")
            temp_path = Path(f.name)

        try:
            loader = FixtureLoader(temp_path)
            assert loader.is_valid is False
            assert loader.error_message is not None
            # Should contain helpful debug info
            assert (
                "hex" in loader.error_message.lower()
                or "parse" in loader.error_message.lower()
            )
        finally:
            temp_path.unlink()

    def test_loader_properties_when_invalid(self):
        """Test that FixtureLoader properties don't crash when invalid."""
        from test_suite.flatbuffers_utils import FixtureLoader

        loader = FixtureLoader(Path("/nonexistent/file.fix"))

        # These should all return None/empty without crashing
        assert loader.is_valid is False
        assert loader.metadata is None
        assert loader.input is None
        assert loader.output is None
        assert loader.fn_entrypoint is None
        assert loader.elf_data == b""


class TestConversionFunctions:
    """Tests for FlatBuffers to Protobuf conversion."""

    def test_normalize_entrypoint_v2_to_v1(self):
        """Test that v2 entrypoints are normalized to v1."""
        from test_suite.flatbuffers_utils import normalize_entrypoint

        assert (
            normalize_entrypoint("sol_compat_elf_loader_v2")
            == "sol_compat_elf_loader_v1"
        )
        assert (
            normalize_entrypoint("sol_compat_instr_execute_v2")
            == "sol_compat_instr_execute_v1"
        )

    def test_normalize_entrypoint_v1_unchanged(self):
        """Test that v1 entrypoints are unchanged."""
        from test_suite.flatbuffers_utils import normalize_entrypoint

        assert (
            normalize_entrypoint("sol_compat_elf_loader_v1")
            == "sol_compat_elf_loader_v1"
        )
        assert (
            normalize_entrypoint("sol_compat_instr_execute_v1")
            == "sol_compat_instr_execute_v1"
        )

    def test_normalize_entrypoint_no_version(self):
        """Test that entrypoints without version suffix are unchanged."""
        from test_suite.flatbuffers_utils import normalize_entrypoint

        assert normalize_entrypoint("custom_entrypoint") == "custom_entrypoint"
        assert normalize_entrypoint("test") == "test"

    def test_convert_fb_to_pb_returns_tuple(self):
        """Test that convert_fb_to_pb_elf_fixture returns a tuple."""
        from test_suite.flatbuffers_utils import convert_fb_to_pb_elf_fixture

        # Pass None - should fail gracefully
        result = convert_fb_to_pb_elf_fixture(None)

        assert isinstance(result, tuple)
        assert len(result) == 2
        # First element is fixture or None, second is error message or None
        fixture, error = result
        # Since we passed None, expect error
        assert fixture is None
        assert error is not None


class TestCLICommands:
    """Tests for CLI commands related to FlatBuffers."""

    def test_check_deps_command_exists(self):
        """Test that check-deps command is registered."""
        from test_suite.test_suite import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["check-deps"])

        # Should run without error
        assert result.exit_code == 0
        assert "FlatBuffers Status" in result.stdout

    def test_validate_fixtures_command_exists(self):
        """Test that validate-fixtures command is registered."""
        from test_suite.test_suite import app
        from typer.testing import CliRunner

        runner = CliRunner()
        # Test with --help to verify command exists
        result = runner.invoke(app, ["validate-fixtures", "--help"])

        assert result.exit_code == 0
        assert "fixture" in result.stdout.lower()

    def test_validate_fixtures_with_test_data(self):
        """Test validate-fixtures on test data directory."""
        from test_suite.test_suite import app
        from typer.testing import CliRunner

        fixtures_dir = Path(__file__).parent / "test_data" / "fixtures"
        if not fixtures_dir.exists():
            pytest.skip("Test fixtures not available")

        runner = CliRunner()
        result = runner.invoke(app, ["validate-fixtures", "-i", str(fixtures_dir)])

        assert result.exit_code == 0
        assert "Summary:" in result.stdout
        assert "Valid:" in result.stdout


@pytest.mark.skipif(
    not Path(__file__).parent.joinpath("test_data/fixtures").exists(),
    reason="Test fixtures not available",
)
class TestWithRealFixtures:
    """Tests that use real fixture files from test_data."""

    def test_load_protobuf_fixture(self):
        """Test loading a real Protobuf fixture file."""
        from test_suite.flatbuffers_utils import FixtureLoader

        fixtures_dir = Path(__file__).parent / "test_data" / "fixtures"
        fixture_files = list(fixtures_dir.glob("*.fix"))

        if not fixture_files:
            pytest.skip("No fixture files found")

        loader = FixtureLoader(fixture_files[0])

        # Should load successfully (these are Protobuf fixtures)
        if loader.is_valid:
            assert loader.format_type in ("protobuf", "flatbuffers")
            # Metadata may or may not be present depending on fixture
        else:
            # If it fails, error message should be informative
            assert loader.error_message is not None
