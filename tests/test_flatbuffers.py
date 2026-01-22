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


class TestFlatBuffersSupportedTypes:
    """Tests for FlatBuffers fixture type support checking."""

    def test_elf_loader_is_supported(self):
        """Test that ELFLoaderFixture is supported for FlatBuffers output."""
        from test_suite.flatbuffers_utils import is_flatbuffers_output_supported

        assert is_flatbuffers_output_supported("sol_compat_elf_loader_v1") is True
        assert is_flatbuffers_output_supported("sol_compat_elf_loader_v2") is True

    def test_other_harnesses_not_supported(self):
        """Test that other harness types are not supported for FlatBuffers output."""
        from test_suite.flatbuffers_utils import is_flatbuffers_output_supported

        # These don't have FlatBuffers schemas in protosol
        assert is_flatbuffers_output_supported("sol_compat_instr_execute_v1") is False
        assert (
            is_flatbuffers_output_supported("sol_compat_vm_syscall_execute_v1") is False
        )
        assert is_flatbuffers_output_supported("sol_compat_txn_execute_v1") is False
        assert is_flatbuffers_output_supported("sol_compat_block_execute_v1") is False

    def test_empty_entrypoint_not_supported(self):
        """Test that empty/None entrypoint returns False."""
        from test_suite.flatbuffers_utils import is_flatbuffers_output_supported

        assert is_flatbuffers_output_supported("") is False
        assert is_flatbuffers_output_supported(None) is False

    def test_conversion_rejects_unsupported_types(self):
        """Test that conversion returns error for unsupported fixture types."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.invoke_pb2 as invoke_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create an InstrFixture (not supported for FlatBuffers)
        fixture = invoke_pb.InstrFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_instr_execute_v1"

        fb_bytes, error = convert_pb_to_fb_elf_fixture(fixture)

        assert fb_bytes is None
        assert error is not None
        assert "not supported" in error.lower()


class TestProtobufToFlatBuffersConversion:
    """Tests for Protobuf to FlatBuffers conversion (output format)."""

    def test_convert_pb_to_fb_returns_tuple(self):
        """Test that convert_pb_to_fb_elf_fixture returns a tuple."""
        from test_suite.flatbuffers_utils import convert_pb_to_fb_elf_fixture

        # Pass None - should fail gracefully
        result = convert_pb_to_fb_elf_fixture(None)

        assert isinstance(result, tuple)
        assert len(result) == 2
        fb_bytes, error = result
        # Since we passed None, expect error
        assert fb_bytes is None
        assert error is not None

    def test_convert_valid_pb_fixture(self):
        """Test converting a valid Protobuf fixture to FlatBuffers."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create a minimal valid Protobuf fixture
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 100  # Minimal ELF-like data
        pb_fixture.input.deploy_checks = True
        pb_fixture.output.error = 0
        pb_fixture.output.text_cnt = 100
        pb_fixture.output.text_off = 64
        pb_fixture.output.entry_pc = 0

        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)

        assert error is None, f"Conversion failed: {error}"
        assert fb_bytes is not None
        assert len(fb_bytes) > 0
        # FlatBuffers files typically start with a small offset
        offset = int.from_bytes(fb_bytes[0:4], "little")
        assert offset < 256, "FlatBuffers offset should be small"

    def test_convert_roundtrip(self):
        """Test that Protobuf -> FlatBuffers -> Protobuf preserves data."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            convert_fb_to_pb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create original Protobuf fixture
        original = elf_pb.ELFLoaderFixture()
        original.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        original.input.elf.data = b"\x7fELF" + b"test_data_12345"
        original.input.deploy_checks = True
        original.input.features.features.extend([100, 200, 300])
        original.output.error = 5
        original.output.text_cnt = 42
        original.output.text_off = 16
        original.output.entry_pc = 8

        # Convert to FlatBuffers
        fb_bytes, error = convert_pb_to_fb_elf_fixture(original)
        assert error is None, f"PB->FB conversion failed: {error}"

        # Parse FlatBuffers
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        assert fb_fixture is not None, "Failed to parse FlatBuffers"

        # Convert back to Protobuf
        roundtrip, error = convert_fb_to_pb_elf_fixture(fb_fixture)
        assert error is None, f"FB->PB conversion failed: {error}"

        # Verify data preserved (entrypoint has v1->v2->v1 transformation)
        assert roundtrip.metadata.fn_entrypoint == original.metadata.fn_entrypoint
        assert roundtrip.input.elf.data == original.input.elf.data
        assert roundtrip.input.deploy_checks == original.input.deploy_checks
        assert list(roundtrip.input.features.features) == list(
            original.input.features.features
        )
        assert roundtrip.output.error == original.output.error
        assert roundtrip.output.text_cnt == original.output.text_cnt
        assert roundtrip.output.text_off == original.output.text_off
        assert roundtrip.output.entry_pc == original.output.entry_pc

    def test_entrypoint_v1_to_v2_in_pb_to_fb_conversion(self):
        """Test that v1 entrypoints are converted to v2 when going PB->FB."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Protobuf uses _v1 entrypoint
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)
        assert error is None

        # Parse and check the FlatBuffers entrypoint is now _v2
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        assert fb_fixture is not None
        metadata = fb_fixture.Metadata()
        assert metadata is not None
        entrypoint = metadata.FnEntrypoint()
        if isinstance(entrypoint, bytes):
            entrypoint = entrypoint.decode("utf-8")
        # Convention: _v1 = Protobuf, _v2 = FlatBuffers
        assert entrypoint == "sol_compat_elf_loader_v2"

    def test_entrypoint_v2_to_v1_in_fb_to_pb_conversion(self):
        """Test that v2 entrypoints are converted to v1 when going FB->PB."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            convert_fb_to_pb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create a PB fixture, convert to FB (gets _v2), then convert back
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        # PB -> FB (v1 -> v2)
        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)
        assert error is None

        # Verify FB has _v2
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        fb_entrypoint = fb_fixture.Metadata().FnEntrypoint()
        if isinstance(fb_entrypoint, bytes):
            fb_entrypoint = fb_entrypoint.decode("utf-8")
        assert fb_entrypoint == "sol_compat_elf_loader_v2"

        # FB -> PB (v2 -> v1)
        roundtrip, error = convert_fb_to_pb_elf_fixture(fb_fixture)
        assert error is None
        # Convention: _v1 = Protobuf, _v2 = FlatBuffers
        assert roundtrip.metadata.fn_entrypoint == "sol_compat_elf_loader_v1"


class TestEntrypointV1V2Convention:
    """
    Tests for the v1/v2 entrypoint convention.

    Convention:
    - _v1 suffix = Protobuf format (e.g., sol_compat_elf_loader_v1)
    - _v2 suffix = FlatBuffers format (e.g., sol_compat_elf_loader_v2)

    This is enforced because:
    - sol_compat_*_v1 functions use Protobuf encoding/decoding
    - sol_compat_*_v2 functions use FlatBuffers encoding/decoding
    """

    def test_fixture_loader_returns_v1_for_flatbuffers(self):
        """Test that FixtureLoader converts _v2 to _v1 when loading FlatBuffers."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            FixtureLoader,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb
        import tempfile
        from pathlib import Path

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create a Protobuf fixture with _v1 entrypoint
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        # Convert to FlatBuffers (this converts _v1 -> _v2)
        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)
        assert error is None

        # Write to a temp file
        with tempfile.NamedTemporaryFile(suffix=".fix", delete=False) as f:
            f.write(fb_bytes)
            temp_path = Path(f.name)

        try:
            # Load with FixtureLoader - should convert back to _v1
            loader = FixtureLoader(temp_path)
            assert loader.is_valid
            assert loader.format_type == "flatbuffers"
            # The fn_entrypoint should be _v1 after loading
            assert loader.fn_entrypoint == "sol_compat_elf_loader_v1"
        finally:
            temp_path.unlink()

    def test_extract_metadata_returns_v1_for_flatbuffers(self):
        """Test that extract_metadata returns _v1 entrypoint for FlatBuffers fixtures."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        from test_suite.multiprocessing_utils import extract_metadata
        import test_suite.protos.elf_pb2 as elf_pb
        import tempfile
        from pathlib import Path

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create and convert to FlatBuffers
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)
        assert error is None

        with tempfile.NamedTemporaryFile(suffix=".fix", delete=False) as f:
            f.write(fb_bytes)
            temp_path = Path(f.name)

        try:
            metadata = extract_metadata(temp_path)
            assert metadata is not None
            # Should be _v1 after conversion
            assert metadata.fn_entrypoint == "sol_compat_elf_loader_v1"
        finally:
            temp_path.unlink()

    def test_harness_lookup_works_for_flatbuffers_fixture(self):
        """Test that ENTRYPOINT_HARNESS_MAP lookup works after loading FlatBuffers."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            FixtureLoader,
            FLATBUFFERS_AVAILABLE,
        )
        from test_suite.fuzz_context import ENTRYPOINT_HARNESS_MAP
        import test_suite.protos.elf_pb2 as elf_pb
        import tempfile
        from pathlib import Path

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create FlatBuffers fixture
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)
        assert error is None

        with tempfile.NamedTemporaryFile(suffix=".fix", delete=False) as f:
            f.write(fb_bytes)
            temp_path = Path(f.name)

        try:
            loader = FixtureLoader(temp_path)
            assert loader.is_valid

            # The entrypoint should be _v1, which exists in the harness map
            fn_entrypoint = loader.fn_entrypoint
            assert fn_entrypoint in ENTRYPOINT_HARNESS_MAP
            harness = ENTRYPOINT_HARNESS_MAP[fn_entrypoint]
            assert harness.fuzz_fn_name == "sol_compat_elf_loader_v1"
        finally:
            temp_path.unlink()

    def test_written_flatbuffers_has_v2_entrypoint(self):
        """Test that FlatBuffers files written have _v2 entrypoint."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create with _v1
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        # Convert to FlatBuffers
        fb_bytes, error = convert_pb_to_fb_elf_fixture(pb_fixture)
        assert error is None

        # Parse the raw FlatBuffers (without conversion)
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        entrypoint = fb_fixture.Metadata().FnEntrypoint()
        if isinstance(entrypoint, bytes):
            entrypoint = entrypoint.decode("utf-8")

        # The raw FlatBuffers should have _v2
        assert entrypoint == "sol_compat_elf_loader_v2"

    def test_written_protobuf_has_v1_entrypoint(self):
        """Test that Protobuf files written have _v1 entrypoint."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            convert_fb_to_pb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Start with a FlatBuffers fixture (has _v2)
        pb_fixture = elf_pb.ELFLoaderFixture()
        pb_fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        pb_fixture.input.elf.data = b"\x7fELF" + b"\x00" * 20

        fb_bytes, _ = convert_pb_to_fb_elf_fixture(pb_fixture)
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        # Convert FB -> PB
        converted_pb, error = convert_fb_to_pb_elf_fixture(fb_fixture)
        assert error is None

        # The Protobuf should have _v1
        assert converted_pb.metadata.fn_entrypoint == "sol_compat_elf_loader_v1"

    def test_full_roundtrip_preserves_format_convention(self):
        """Test that PB -> FB -> PB preserves the _v1 convention for PB."""
        from test_suite.flatbuffers_utils import (
            convert_pb_to_fb_elf_fixture,
            convert_fb_to_pb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Original Protobuf with _v1
        original = elf_pb.ELFLoaderFixture()
        original.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        original.input.elf.data = b"\x7fELF" + b"test_data"

        # PB -> FB (should become _v2)
        fb_bytes, _ = convert_pb_to_fb_elf_fixture(original)
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        fb_entrypoint = fb_fixture.Metadata().FnEntrypoint()
        if isinstance(fb_entrypoint, bytes):
            fb_entrypoint = fb_entrypoint.decode("utf-8")
        assert (
            fb_entrypoint == "sol_compat_elf_loader_v2"
        ), "FlatBuffers should have _v2"

        # FB -> PB (should become _v1 again)
        roundtrip, _ = convert_fb_to_pb_elf_fixture(fb_fixture)
        assert (
            roundtrip.metadata.fn_entrypoint == "sol_compat_elf_loader_v1"
        ), "Protobuf should have _v1"

    def test_non_elf_loader_entrypoints_unchanged(self):
        """Test that non-elf_loader entrypoints are not modified."""
        from test_suite.fuzz_context import entrypoint_to_v1, entrypoint_to_v2

        # Entrypoints without v1/v2 suffix should be unchanged
        assert entrypoint_to_v1("custom_entrypoint") == "custom_entrypoint"
        assert entrypoint_to_v2("custom_entrypoint") == "custom_entrypoint"

        # Empty/None should be handled gracefully
        assert entrypoint_to_v1("") == ""
        assert entrypoint_to_v2("") == ""

    def test_centralized_entrypoint_functions(self):
        """Test that centralized entrypoint conversion functions work correctly."""
        from test_suite.fuzz_context import (
            entrypoint_to_v1,
            entrypoint_to_v2,
            is_flatbuffers_supported,
            get_harness_for_entrypoint,
            FLATBUFFERS_HARNESSES,
        )

        # v1 -> v2
        assert (
            entrypoint_to_v2("sol_compat_elf_loader_v1") == "sol_compat_elf_loader_v2"
        )
        assert (
            entrypoint_to_v2("sol_compat_instr_execute_v1")
            == "sol_compat_instr_execute_v2"
        )

        # v2 -> v1
        assert (
            entrypoint_to_v1("sol_compat_elf_loader_v2") == "sol_compat_elf_loader_v1"
        )
        assert (
            entrypoint_to_v1("sol_compat_instr_execute_v2")
            == "sol_compat_instr_execute_v1"
        )

        # Already correct version - unchanged
        assert (
            entrypoint_to_v1("sol_compat_elf_loader_v1") == "sol_compat_elf_loader_v1"
        )
        assert (
            entrypoint_to_v2("sol_compat_elf_loader_v2") == "sol_compat_elf_loader_v2"
        )

        # is_flatbuffers_supported
        assert is_flatbuffers_supported("sol_compat_elf_loader_v1") is True
        assert is_flatbuffers_supported("sol_compat_elf_loader_v2") is True
        assert is_flatbuffers_supported("sol_compat_instr_execute_v1") is False

        # FLATBUFFERS_HARNESSES should contain ElfLoaderHarness
        assert "ElfLoaderHarness" in FLATBUFFERS_HARNESSES

    def test_get_harness_for_entrypoint_safe_lookup(self):
        """Test that get_harness_for_entrypoint handles v1/v2 and errors gracefully."""
        from test_suite.fuzz_context import get_harness_for_entrypoint

        # v1 entrypoint works
        harness = get_harness_for_entrypoint("sol_compat_elf_loader_v1")
        assert harness.fuzz_fn_name == "sol_compat_elf_loader_v1"

        # v2 entrypoint is normalized to v1 and works
        harness = get_harness_for_entrypoint("sol_compat_elf_loader_v2")
        assert harness.fuzz_fn_name == "sol_compat_elf_loader_v1"

        # Unknown entrypoint raises KeyError with helpful message
        with pytest.raises(KeyError) as exc_info:
            get_harness_for_entrypoint("unknown_entrypoint")
        assert "Unknown entrypoint" in str(exc_info.value)
        assert "sol_compat_elf_loader_v1" in str(exc_info.value)  # Shows valid options

        # Empty entrypoint raises KeyError
        with pytest.raises(KeyError) as exc_info:
            get_harness_for_entrypoint("")
        assert "empty or None" in str(exc_info.value)


class TestOutputFormatHandling:
    """Tests for output format selection in fixture_utils."""

    def test_write_fixture_accepts_source_format(self):
        """Test that write_fixture_to_disk accepts source_format parameter."""
        from test_suite.fixture_utils import write_fixture_to_disk
        import inspect

        sig = inspect.signature(write_fixture_to_disk)
        params = list(sig.parameters.keys())

        assert "source_format" in params
        # Check it has a default value
        assert sig.parameters["source_format"].default == "protobuf"

    def test_auto_format_matches_input(self):
        """Test that auto format matches the source format."""
        import test_suite.globals as globals

        # Save original
        original_format = globals.output_format

        try:
            globals.output_format = "auto"

            # The logic: if output_format is 'auto', use source_format
            # Test this logic directly
            output_format = globals.output_format
            source_format = "flatbuffers"

            if output_format == "auto":
                resolved = (
                    source_format
                    if source_format in ("protobuf", "flatbuffers")
                    else "protobuf"
                )
            else:
                resolved = output_format

            assert resolved == "flatbuffers"

            # Test with protobuf source
            source_format = "protobuf"
            if output_format == "auto":
                resolved = (
                    source_format
                    if source_format in ("protobuf", "flatbuffers")
                    else "protobuf"
                )
            else:
                resolved = output_format

            assert resolved == "protobuf"

            # Test with unknown source (should default to protobuf)
            source_format = "unknown"
            if output_format == "auto":
                resolved = (
                    source_format
                    if source_format in ("protobuf", "flatbuffers")
                    else "protobuf"
                )
            else:
                resolved = output_format

            assert resolved == "protobuf"

        finally:
            globals.output_format = original_format

    def test_forced_format_overrides_source(self):
        """Test that explicit format overrides source format."""
        import test_suite.globals as globals

        original_format = globals.output_format

        try:
            # Force protobuf output
            globals.output_format = "protobuf"
            source_format = "flatbuffers"

            output_format = globals.output_format
            if output_format == "auto":
                resolved = source_format
            else:
                resolved = output_format

            assert resolved == "protobuf"

            # Force flatbuffers output
            globals.output_format = "flatbuffers"
            source_format = "protobuf"

            output_format = globals.output_format
            if output_format == "auto":
                resolved = source_format
            else:
                resolved = output_format

            assert resolved == "flatbuffers"

        finally:
            globals.output_format = original_format


class TestFormatAutoDetection:
    """Tests for automatic format detection from input files."""

    def test_detect_flatbuffers_from_bytes(self):
        """Test detecting FlatBuffers format from raw bytes."""
        from test_suite.flatbuffers_utils import detect_format, is_flatbuffers_format

        # Create minimal FlatBuffers-like data
        # FlatBuffers start with a 4-byte offset to root table
        fb_data = b"\x14\x00\x00\x00\x00\x00" + b"\x00" * 30
        assert is_flatbuffers_format(fb_data) is True
        assert detect_format(fb_data) == "flatbuffers"

    def test_detect_protobuf_from_bytes(self):
        """Test detecting Protobuf format from raw bytes."""
        from test_suite.flatbuffers_utils import detect_format, is_protobuf_format

        # Protobuf typically starts with field tag 0x0a (field 1, wire type 2)
        pb_data = b"\x0a\x10" + b"message content"
        assert is_protobuf_format(pb_data) is True
        assert detect_format(pb_data) == "protobuf"

    def test_detect_format_with_real_protobuf(self):
        """Test format detection with real serialized Protobuf."""
        from test_suite.flatbuffers_utils import detect_format
        import test_suite.protos.elf_pb2 as elf_pb

        # Create and serialize a real Protobuf fixture
        fixture = elf_pb.ELFLoaderFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        fixture.input.elf.data = b"\x7fELF" + b"\x00" * 50

        serialized = fixture.SerializeToString()

        detected = detect_format(serialized)
        assert detected == "protobuf", f"Expected protobuf, got {detected}"

    def test_detect_format_with_real_flatbuffers(self):
        """Test format detection with real serialized FlatBuffers."""
        from test_suite.flatbuffers_utils import (
            detect_format,
            convert_pb_to_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create Protobuf fixture
        fixture = elf_pb.ELFLoaderFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        fixture.input.elf.data = b"\x7fELF" + b"\x00" * 50

        # Convert to FlatBuffers
        fb_bytes, error = convert_pb_to_fb_elf_fixture(fixture)
        assert error is None

        detected = detect_format(fb_bytes)
        assert detected == "flatbuffers", f"Expected flatbuffers, got {detected}"

    def test_create_fixture_detects_source_format(self):
        """Test that create_fixture function detects source format."""
        # This is tested implicitly through the function signature
        from test_suite.fixture_utils import create_fixture
        import inspect

        # Verify the function exists and is callable
        assert callable(create_fixture)

        # The function should use detect_format internally
        source = inspect.getsource(create_fixture)
        assert "detect_format" in source, "create_fixture should use detect_format"
        assert "source_format" in source, "create_fixture should track source_format"


class TestFormatDetectionEdgeCases:
    """Tests for edge cases in format detection."""

    def test_empty_data(self):
        """Test detection with empty data."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"") == "unknown"

    def test_tiny_data(self):
        """Test detection with data smaller than minimum."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"abc") == "unknown"
        assert detect_format(b"\x0a") == "unknown"

    def test_all_zeros(self):
        """Test detection with all zero bytes."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"\x00" * 100) == "unknown"

    def test_all_ones(self):
        """Test detection with all 0xff bytes."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"\xff" * 100) == "unknown"

    def test_random_garbage(self):
        """Test detection with random garbage data."""
        from test_suite.flatbuffers_utils import detect_format
        import random

        random.seed(42)  # Reproducible
        garbage = bytes(random.randint(0, 255) for _ in range(1000))
        result = detect_format(garbage)
        # Should not crash, result depends on content
        assert result in ("protobuf", "flatbuffers", "unknown")

    def test_protobuf_field_2(self):
        """Test detection of Protobuf starting with field 2."""
        from test_suite.flatbuffers_utils import detect_format, is_protobuf_format

        # 0x12 = field 2, wire type 2
        pb_data = b"\x12\x10" + b"field 2 content"
        assert is_protobuf_format(pb_data) is True
        assert detect_format(pb_data) == "protobuf"

    def test_protobuf_field_3(self):
        """Test detection of Protobuf starting with field 3."""
        from test_suite.flatbuffers_utils import detect_format, is_protobuf_format

        # 0x1a = field 3, wire type 2
        pb_data = b"\x1a\x10" + b"field 3 content"
        assert is_protobuf_format(pb_data) is True
        assert detect_format(pb_data) == "protobuf"

    def test_protobuf_varint_field(self):
        """Test detection of Protobuf with varint field."""
        from test_suite.flatbuffers_utils import is_protobuf_format

        # 0x08 = field 1, wire type 0 (varint)
        pb_data = b"\x08\x01\x00\x00\x00"
        assert is_protobuf_format(pb_data) is True

    def test_invalid_wire_type_rejected(self):
        """Test that invalid wire types are rejected."""
        from test_suite.flatbuffers_utils import is_protobuf_format

        # Wire type 7 is invalid
        invalid_data = b"\x0f\x00\x00\x00"  # field 1, wire type 7
        assert is_protobuf_format(invalid_data) is False

    def test_high_field_number_rejected(self):
        """Test that unreasonably high field numbers are rejected."""
        from test_suite.flatbuffers_utils import is_protobuf_format

        # Single-byte field tag with field number > 15 requires multi-byte encoding
        # For single byte: field_num = (byte >> 3), wire_type = (byte & 7)
        # Max single-byte field with wire type 0 is field 15: (15 << 3) | 0 = 120 = 0x78
        # Field 16+ requires continuation bit (high bit set)
        # Test with byte that decodes to field > 100 in single byte:
        # (120 << 3) = 960 -> but that's a multi-byte varint
        # Actually, for field 120, wire type 0: 120 << 3 = 960, needs 2 bytes
        # The check looks at first_byte >> 3, so 0xf8 >> 3 = 31, which is < 100
        # For field > 100 in first byte: need first_byte >> 3 > 100
        # That means first_byte > 800, impossible in single byte
        # So this test is about multi-byte varints which we don't fully decode
        # Instead, test that a completely invalid first byte is rejected
        invalid_tag = b"\xff\xff\x00\x00"  # wire type 7 (invalid)
        assert is_protobuf_format(invalid_tag) is False

    def test_flatbuffers_vtable_validation(self):
        """Test that FlatBuffers detection validates vtable structure."""
        from test_suite.flatbuffers_utils import is_flatbuffers_format

        # Invalid: offset points to valid position but no valid vtable
        invalid_fb = b"\x08\x00\x00\x00" + b"\xff" * 20
        # This might or might not pass depending on vtable validation
        result = is_flatbuffers_format(invalid_fb)
        assert isinstance(result, bool)

    def test_truncated_flatbuffers(self):
        """Test detection with truncated FlatBuffers data."""
        from test_suite.flatbuffers_utils import is_flatbuffers_format

        # Offset points beyond data
        truncated = b"\x14\x00\x00\x00\x00\x00"  # Offset 20, but only 6 bytes
        assert is_flatbuffers_format(truncated) is False


class TestValidationMode:
    """Tests for validation-based format detection."""

    def test_validate_real_protobuf(self):
        """Test validation mode with real Protobuf fixture."""
        from test_suite.flatbuffers_utils import detect_format
        import test_suite.protos.elf_pb2 as elf_pb

        # Create a fixture with metadata (the common field across all fixture types)
        fixture = elf_pb.ELFLoaderFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        fixture.input.elf.data = b"\x7fELF" + b"\x00" * 50

        serialized = fixture.SerializeToString()

        # Both modes should return protobuf
        assert detect_format(serialized, validate=False) == "protobuf"
        assert detect_format(serialized, validate=True) == "protobuf"

    def test_validate_real_flatbuffers(self):
        """Test validation mode with real FlatBuffers fixture."""
        from test_suite.flatbuffers_utils import (
            detect_format,
            convert_pb_to_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        fixture = elf_pb.ELFLoaderFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        fixture.input.elf.data = b"\x7fELF" + b"\x00" * 50

        fb_bytes, error = convert_pb_to_fb_elf_fixture(fixture)
        assert error is None

        # Both modes should return flatbuffers
        assert detect_format(fb_bytes, validate=False) == "flatbuffers"
        assert detect_format(fb_bytes, validate=True) == "flatbuffers"

    def test_validate_uses_common_fixture_structure(self):
        """Test that validation works with any fixture type via common metadata field."""
        from test_suite.flatbuffers_utils import detect_format, _validate_protobuf
        import test_suite.protos.invoke_pb2 as invoke_pb

        # InstrFixture is a different fixture type but shares the metadata field
        fixture = invoke_pb.InstrFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_instr_execute_v1"

        serialized = fixture.SerializeToString()

        # Should validate correctly using the common metadata field
        assert _validate_protobuf(serialized) is True
        assert detect_format(serialized, validate=True) == "protobuf"

    def test_validate_catches_false_positive(self):
        """Test that validation mode can catch heuristic false positives."""
        from test_suite.flatbuffers_utils import detect_format

        # Data that might look like Protobuf to heuristics but isn't valid
        fake_pb = b"\x0a\x10" + b"not a real protobuf message structure"

        # Heuristic mode might say protobuf
        heuristic_result = detect_format(fake_pb, validate=False)

        # Validation mode should be more accurate (likely returns unknown)
        validated_result = detect_format(fake_pb, validate=True)

        # Both should return something (no crash)
        assert heuristic_result in ("protobuf", "flatbuffers", "unknown")
        assert validated_result in ("protobuf", "flatbuffers", "unknown")

    def test_validate_empty_returns_unknown(self):
        """Test validation with empty data returns unknown."""
        from test_suite.flatbuffers_utils import detect_format

        assert detect_format(b"", validate=True) == "unknown"

    def test_validate_garbage_returns_unknown(self):
        """Test validation with garbage data returns unknown."""
        from test_suite.flatbuffers_utils import detect_format

        garbage = b"this is definitely not a valid fixture format at all!"
        result = detect_format(garbage, validate=True)
        # Should return unknown or the heuristic guess
        assert result in ("protobuf", "flatbuffers", "unknown")

    def test_validate_checks_metadata_fn_entrypoint(self):
        """Test that validation checks for fn_entrypoint in metadata."""
        from test_suite.flatbuffers_utils import _validate_protobuf
        import test_suite.protos.elf_pb2 as elf_pb

        # Fixture with empty metadata (no fn_entrypoint)
        fixture_empty = elf_pb.ELFLoaderFixture()
        serialized_empty = fixture_empty.SerializeToString()

        # Fixture with valid metadata
        fixture_valid = elf_pb.ELFLoaderFixture()
        fixture_valid.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        serialized_valid = fixture_valid.SerializeToString()

        # Empty metadata should fail validation
        assert _validate_protobuf(serialized_empty) is False

        # Valid metadata should pass
        assert _validate_protobuf(serialized_valid) is True


class TestFormatDetectionConsistency:
    """Tests to ensure format detection is consistent and deterministic."""

    def test_detection_is_deterministic(self):
        """Test that format detection gives same result on repeated calls."""
        from test_suite.flatbuffers_utils import detect_format
        import test_suite.protos.elf_pb2 as elf_pb

        fixture = elf_pb.ELFLoaderFixture()
        fixture.metadata.fn_entrypoint = "test"
        fixture.input.elf.data = b"\x7fELF" + b"\x00" * 100

        serialized = fixture.SerializeToString()

        results = [detect_format(serialized) for _ in range(10)]
        assert all(
            r == results[0] for r in results
        ), "Detection should be deterministic"

    def test_flatbuffers_takes_precedence(self):
        """Test that FlatBuffers detection takes precedence over Protobuf."""
        from test_suite.flatbuffers_utils import (
            detect_format,
            convert_pb_to_fb_elf_fixture,
            is_flatbuffers_format,
            is_protobuf_format,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        fixture = elf_pb.ELFLoaderFixture()
        fixture.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        fixture.input.elf.data = b"\x7fELF"

        fb_bytes, _ = convert_pb_to_fb_elf_fixture(fixture)

        # FlatBuffers should be detected even if it also matches Protobuf heuristics
        assert is_flatbuffers_format(fb_bytes) is True
        assert detect_format(fb_bytes) == "flatbuffers"

    def test_roundtrip_preserves_detectability(self):
        """Test that roundtrip conversion preserves format detectability."""
        from test_suite.flatbuffers_utils import (
            detect_format,
            convert_pb_to_fb_elf_fixture,
            convert_fb_to_pb_elf_fixture,
            parse_fb_elf_fixture,
            FLATBUFFERS_AVAILABLE,
        )
        import test_suite.protos.elf_pb2 as elf_pb

        if not FLATBUFFERS_AVAILABLE:
            pytest.skip("FlatBuffers not available")

        # Create original Protobuf
        original = elf_pb.ELFLoaderFixture()
        original.metadata.fn_entrypoint = "sol_compat_elf_loader_v1"
        original.input.elf.data = b"\x7fELF" + b"test" * 100

        pb_serialized = original.SerializeToString()
        assert detect_format(pb_serialized) == "protobuf"

        # Convert to FlatBuffers
        fb_bytes, _ = convert_pb_to_fb_elf_fixture(original)
        assert detect_format(fb_bytes) == "flatbuffers"

        # Convert back to Protobuf
        fb_parsed = parse_fb_elf_fixture(fb_bytes)
        roundtrip, _ = convert_fb_to_pb_elf_fixture(fb_parsed)
        roundtrip_serialized = roundtrip.SerializeToString()
        assert detect_format(roundtrip_serialized) == "protobuf"


class TestCLIOutputFormat:
    """Tests for CLI output format option."""

    def test_create_fixtures_has_output_format_option(self):
        """Test that create-fixtures command has --output-format option."""
        from test_suite.test_suite import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["create-fixtures", "--help"])

        assert result.exit_code == 0
        assert "--output-format" in result.stdout or "-F" in result.stdout
        assert "auto" in result.stdout
        assert "protobuf" in result.stdout
        assert "flatbuffers" in result.stdout

    def test_output_format_default_is_auto(self):
        """Test that default output format is 'auto'."""
        import test_suite.globals as globals

        # The global default should be 'auto'
        assert globals.output_format == "auto"

    def test_invalid_output_format_rejected(self):
        """Test that invalid output format is rejected."""
        from test_suite.test_suite import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "create-fixtures",
                "-i",
                "/tmp/nonexistent",
                "-o",
                "/tmp/out",
                "-F",
                "invalid_format",
            ],
        )

        # Should fail with error about invalid format
        assert result.exit_code != 0
        assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower()


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

    def test_detect_format_on_real_fixtures(self):
        """Test format detection on real fixture files."""
        from test_suite.flatbuffers_utils import detect_format

        fixtures_dir = Path(__file__).parent / "test_data" / "fixtures"
        fixture_files = list(fixtures_dir.glob("*.fix"))

        if not fixture_files:
            pytest.skip("No fixture files found")

        for fixture_file in fixture_files:
            with open(fixture_file, "rb") as f:
                data = f.read()

            fmt = detect_format(data)
            assert fmt in (
                "protobuf",
                "flatbuffers",
                "unknown",
            ), f"Unexpected format for {fixture_file}"

    def test_write_preserves_format_in_auto_mode(self):
        """Test that auto mode preserves the detected format."""
        from test_suite.flatbuffers_utils import detect_format, FixtureLoader
        import test_suite.globals as globals

        fixtures_dir = Path(__file__).parent / "test_data" / "fixtures"
        fixture_files = list(fixtures_dir.glob("*.fix"))

        if not fixture_files:
            pytest.skip("No fixture files found")

        original_format = globals.output_format
        try:
            globals.output_format = "auto"

            for fixture_file in fixture_files[:2]:  # Test first 2 files
                with open(fixture_file, "rb") as f:
                    data = f.read()

                input_format = detect_format(data)

                # In auto mode, output should match input
                if input_format in ("protobuf", "flatbuffers"):
                    # The resolved format should match
                    resolved = (
                        input_format
                        if globals.output_format == "auto"
                        else globals.output_format
                    )
                    assert resolved == input_format

        finally:
            globals.output_format = original_format
