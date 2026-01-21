"""
FlatBuffers to Protobuf conversion utilities for solana-conformance.

This module provides:
1. Detection of FlatBuffers vs Protobuf format
2. Parsing of FlatBuffers files
3. Conversion from FlatBuffers to Protobuf for downstream processing

This consolidates and extends the existing elf_proto_converter.py functionality
to support both Protobuf and FlatBuffers input formats.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, Any, Union
from google.protobuf.message import DecodeError


# ============================================================================
# Dependency Checks with User-Friendly Error Messages
# ============================================================================


def _check_flatbuffers_package():
    """Check if the flatbuffers Python package is installed."""
    try:
        import flatbuffers

        return True, (
            flatbuffers.__version__
            if hasattr(flatbuffers, "__version__")
            else "unknown"
        )
    except ImportError:
        return False, None


def _check_numpy_package():
    """Check if numpy is installed (optional, for performance)."""
    try:
        import numpy

        return True, numpy.__version__
    except ImportError:
        return False, None


def _get_fb_bindings_path() -> Path:
    """Get the path where FlatBuffers bindings should be."""
    return Path(__file__).parent / "flatbuffers"


def _check_fb_bindings_exist() -> Tuple[bool, Optional[str]]:
    """Check if FlatBuffers bindings have been generated."""
    fb_path = _get_fb_bindings_path()

    # Check for the expected directory structure
    expected_path = fb_path / "org" / "solana" / "sealevel" / "v2"
    if not expected_path.exists():
        return False, f"FlatBuffers bindings not found at: {expected_path}"

    # Check for at least one generated file
    expected_file = expected_path / "ELFLoaderFixture.py"
    if not expected_file.exists():
        return False, f"Missing generated file: {expected_file}"

    return True, None


def get_dependency_status() -> dict:
    """
    Check all dependencies and return a status report.

    Useful for debugging and troubleshooting.

    Returns:
        dict with keys: 'flatbuffers_package', 'numpy_package', 'fb_bindings', 'ready'
    """
    fb_pkg_ok, fb_pkg_ver = _check_flatbuffers_package()
    np_ok, np_ver = _check_numpy_package()
    bindings_ok, bindings_err = _check_fb_bindings_exist()

    return {
        "flatbuffers_package": {"installed": fb_pkg_ok, "version": fb_pkg_ver},
        "numpy_package": {"installed": np_ok, "version": np_ver},
        "fb_bindings": {"generated": bindings_ok, "error": bindings_err},
        "ready": fb_pkg_ok and bindings_ok,
    }


def print_dependency_status():
    """Print a human-readable dependency status report."""
    status = get_dependency_status()

    print("\n=== solana-conformance FlatBuffers Status ===\n")

    # FlatBuffers package
    if status["flatbuffers_package"]["installed"]:
        print(f"[OK] flatbuffers package: v{status['flatbuffers_package']['version']}")
    else:
        print("[MISSING] flatbuffers package: NOT INSTALLED")
        print("   Fix: pip install flatbuffers>=24.0.0")

    # Numpy (optional)
    if status["numpy_package"]["installed"]:
        print(
            f"[OK] numpy package: v{status['numpy_package']['version']} (faster parsing)"
        )
    else:
        print("[OPTIONAL] numpy package: not installed (improves performance)")
        print("   Optional: pip install numpy>=1.24.0")

    # FlatBuffers bindings
    if status["fb_bindings"]["generated"]:
        print("[OK] FlatBuffers bindings: generated")
    else:
        print("[MISSING] FlatBuffers bindings: NOT GENERATED")
        print(f"   Error: {status['fb_bindings']['error']}")
        print("   Fix: cd solana-conformance && ./generate_flatbuffers.sh")

    print()
    if status["ready"]:
        print("[OK] FlatBuffers support is ready!")
    else:
        print("[ERROR] FlatBuffers support is NOT ready. See above for fixes.")
    print()

    return status["ready"]


# Add the flatbuffers generated code to the path
_FB_PATH = _get_fb_bindings_path()
if str(_FB_PATH) not in sys.path:
    sys.path.insert(0, str(_FB_PATH))

# Import Protobuf types
import test_suite.protos.elf_pb2 as elf_pb
import test_suite.protos.metadata_pb2 as metadata_pb

# Check if flatbuffers package is installed
_FB_PKG_OK, _FB_PKG_VER = _check_flatbuffers_package()
if not _FB_PKG_OK:
    print(
        "\nWarning: FlatBuffers package not installed. FlatBuffers fixtures won't be readable.\n"
        "   To install: pip install flatbuffers>=24.0.0\n"
        "   Or re-run:  source install.sh  (or install_ubuntu.sh)\n"
    )

# Try to import FlatBuffers types (generated)
FLATBUFFERS_AVAILABLE = False
_FB_IMPORT_ERROR = None

if _FB_PKG_OK:
    try:
        from org.solana.sealevel.v2.ELFLoaderFixture import (
            ELFLoaderFixture as FB_ELFLoaderFixture,
        )
        from org.solana.sealevel.v2.ELFLoaderCtx import ELFLoaderCtx as FB_ELFLoaderCtx
        from org.solana.sealevel.v2.ELFLoaderEffects import (
            ELFLoaderEffects as FB_ELFLoaderEffects,
        )
        from org.solana.sealevel.v2.FixtureMetadata import (
            FixtureMetadata as FB_FixtureMetadata,
        )
        from org.solana.sealevel.v2.FeatureSet import FeatureSet as FB_FeatureSet

        FLATBUFFERS_AVAILABLE = True
    except ImportError as e:
        _FB_IMPORT_ERROR = str(e)
        # Only print if bindings don't exist (not just missing import)
        bindings_ok, _ = _check_fb_bindings_exist()
        if not bindings_ok:
            print(
                "\nWarning: FlatBuffers bindings not generated. FlatBuffers fixtures won't be readable.\n"
                "   To generate: cd solana-conformance && ./generate_flatbuffers.sh\n"
                f"   (Error: {e})\n"
            )
        else:
            print(f"Warning: FlatBuffers import error: {e}")


# ============================================================================
# Format Detection
# ============================================================================


def is_flatbuffers_format(data: bytes) -> bool:
    """
    Detect if the data is in FlatBuffers format.

    FlatBuffers files start with a 4-byte little-endian root table offset,
    typically small (< 256). We check for common patterns.

    Args:
        data: Raw bytes to check

    Returns:
        True if likely FlatBuffers format, False otherwise
    """
    if len(data) < 8:
        return False

    # FlatBuffers files start with a 4-byte little-endian offset to the root table
    offset = int.from_bytes(data[0:4], "little")

    # Valid offsets are typically 4-256 bytes from start
    if offset < 4 or offset > 1024:
        return False

    # Check if offset points to a valid position
    if offset >= len(data):
        return False

    # Common FlatBuffers patterns:
    # 0x14 0x00 0x00 0x00 (offset = 20)
    # Followed by 0x00 0x00 or 0x0a 0x00
    if len(data) > 6:
        if data[4] == 0x00 and data[5] == 0x00:
            return True
        if data[4:6] == b"\x0a\x00":
            return True
        if data[0] == 0x14 and data[1] == 0x00 and data[2] == 0x00 and data[3] == 0x00:
            return True

    return False


def is_protobuf_format(data: bytes) -> bool:
    """
    Detect if the data is in Protobuf format.

    Protobuf messages typically start with field tags.
    Field 1 with wire type 2 (length-delimited) = 0x0a

    Args:
        data: Raw bytes to check

    Returns:
        True if likely Protobuf format, False otherwise
    """
    if len(data) < 2:
        return False

    # 0x0a = field 1, wire type 2 (embedded message/string/bytes)
    return data[0] == 0x0A


def detect_format(data: bytes) -> str:
    """
    Detect the format of binary data.

    Args:
        data: Raw bytes to check

    Returns:
        'flatbuffers', 'protobuf', or 'unknown'
    """
    if is_flatbuffers_format(data):
        return "flatbuffers"
    elif is_protobuf_format(data):
        return "protobuf"
    else:
        return "unknown"


# ============================================================================
# FlatBuffers Byte Array Helpers (numpy for performance)
# ============================================================================

# Try to import numpy for faster array operations
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def _get_fb_byte_array(obj, get_fn, length_fn, numpy_fn=None) -> bytes:
    """
    Extract a byte array from a FlatBuffers object.

    Uses numpy when available for better performance.

    Args:
        obj: FlatBuffers object
        get_fn: Function that takes index and returns byte
        length_fn: Function that returns length
        numpy_fn: Optional function that returns numpy array directly

    Returns:
        bytes object
    """
    length = length_fn()
    if length == 0:
        return b""

    # Use numpy method if available (faster)
    if NUMPY_AVAILABLE and numpy_fn is not None:
        try:
            arr = numpy_fn()
            if arr is not None and hasattr(arr, "tobytes"):
                return arr.tobytes()
        except Exception:
            pass  # Fall back to manual iteration

    # Manual iteration fallback
    return bytes(get_fn(i) for i in range(length))


def _get_fb_uint64_array(obj, get_fn, length_fn, numpy_fn=None) -> list:
    """
    Extract a uint64 array from a FlatBuffers object.

    Uses numpy when available for better performance.

    Args:
        obj: FlatBuffers object
        get_fn: Function that takes index and returns uint64
        length_fn: Function that returns length
        numpy_fn: Optional function that returns numpy array directly

    Returns:
        list of uint64 values
    """
    length = length_fn()
    if length == 0:
        return []

    # Use numpy method if available (faster)
    if NUMPY_AVAILABLE and numpy_fn is not None:
        try:
            arr = numpy_fn()
            if arr is not None and hasattr(arr, "tolist"):
                return arr.tolist()
        except Exception:
            pass  # Fall back to manual iteration

    # Manual iteration fallback
    return [get_fn(i) for i in range(length)]


# ============================================================================
# FlatBuffers Parsing
# ============================================================================


def parse_fb_elf_fixture(data: bytes) -> Optional[Any]:
    """
    Parse FlatBuffers ELFLoaderFixture from raw bytes.

    Args:
        data: FlatBuffers encoded data

    Returns:
        Parsed ELFLoaderFixture object or None if parsing fails
    """
    if not FLATBUFFERS_AVAILABLE:
        return None

    try:
        fixture = FB_ELFLoaderFixture.GetRootAs(data, 0)
        return fixture
    except Exception as e:
        print(f"Failed to parse FlatBuffers: {e}")
        return None


# ============================================================================
# Entrypoint Normalization
# ============================================================================


def normalize_entrypoint(entrypoint: str) -> str:
    """
    Normalize FlatBuffers v2 entrypoints to Protobuf v1 entrypoints.

    FlatBuffers schema uses _v2 suffix, but the harness map expects _v1.

    Args:
        entrypoint: The original entrypoint name

    Returns:
        Normalized entrypoint name
    """
    if entrypoint and entrypoint.endswith("_v2"):
        return entrypoint[:-3] + "_v1"
    return entrypoint


# ============================================================================
# FlatBuffers to Protobuf Conversion
# ============================================================================


def convert_fb_to_pb_elf_fixture(
    fb_fixture,
) -> Tuple[Optional[elf_pb.ELFLoaderFixture], Optional[str]]:
    """
    Convert a FlatBuffers ELFLoaderFixture to Protobuf ELFLoaderFixture.

    Args:
        fb_fixture: Parsed FlatBuffers ELFLoaderFixture

    Returns:
        Tuple of (Protobuf ELFLoaderFixture, error_message).
        On success: (fixture, None)
        On failure: (None, error_message)
    """
    try:
        pb_fixture = elf_pb.ELFLoaderFixture()

        # Convert metadata
        fb_metadata = fb_fixture.Metadata()
        if fb_metadata:
            fn_entrypoint = fb_metadata.FnEntrypoint()
            if fn_entrypoint:
                entrypoint_str = (
                    fn_entrypoint.decode("utf-8")
                    if isinstance(fn_entrypoint, bytes)
                    else fn_entrypoint
                )
                # Normalize v2 entrypoints to v1 for harness compatibility
                pb_fixture.metadata.fn_entrypoint = normalize_entrypoint(entrypoint_str)

        # Convert input (ELFLoaderCtx)
        fb_input = fb_fixture.Input()
        if fb_input:
            # Get ELF data (use numpy method when available for speed)
            elf_data_len = fb_input.ElfDataLength()
            if elf_data_len > 0:
                elf_data = _get_fb_byte_array(
                    fb_input,
                    fb_input.ElfData,
                    fb_input.ElfDataLength,
                    numpy_fn=(
                        fb_input.ElfDataAsNumpy
                        if hasattr(fb_input, "ElfDataAsNumpy")
                        else None
                    ),
                )
                pb_fixture.input.elf.data = elf_data

            # Get features
            fb_features = fb_input.Features()
            if fb_features:
                features_len = fb_features.FeaturesLength()
                for i in range(features_len):
                    pb_fixture.input.features.features.append(fb_features.Features(i))

            # Get deploy_checks
            pb_fixture.input.deploy_checks = fb_input.DeployChecks()

        # Convert output (ELFLoaderEffects)
        fb_output = fb_fixture.Output()
        if fb_output:
            pb_fixture.output.error = fb_output.ErrCode()
            pb_fixture.output.text_cnt = fb_output.TextCnt()
            pb_fixture.output.text_off = fb_output.TextOff()
            pb_fixture.output.entry_pc = fb_output.EntryPc()

            # Get rodata_hash (XXHash is 8 bytes) - use as rodata placeholder
            fb_rodata_hash = fb_output.RodataHash()
            if fb_rodata_hash:
                rodata_hash_bytes = bytes(fb_rodata_hash.Hash())
                pb_fixture.output.rodata = rodata_hash_bytes

        return pb_fixture, None
    except Exception as e:
        return None, f"FlatBuffers conversion error: {type(e).__name__}: {e}"


# ============================================================================
# Unified Fixture Loading (supports both formats)
# ============================================================================


class FixtureLoader:
    """
    Unified fixture loader that handles both Protobuf and FlatBuffers formats.

    This consolidates the functionality from elf_proto_converter.py and adds
    FlatBuffers support.

    Example:
        >>> loader = FixtureLoader(Path('fixture.fix'))
        >>> if loader.is_valid:
        ...     print(f"Format: {loader.format_type}")
        ...     print(f"Entrypoint: {loader.fn_entrypoint}")
        >>> else:
        ...     print(f"Failed: {loader.error_message}")
    """

    def __init__(self, filepath: Path):
        """
        Load a fixture file, automatically detecting format.

        Args:
            filepath: Path to the fixture file
        """
        self.filepath = filepath
        self.format_type = "unknown"
        self.pb_fixture: Optional[elf_pb.ELFLoaderFixture] = None
        self.raw_data: bytes = b""
        self.error_message: Optional[str] = None

        self._load()

    def _load(self):
        """Load and parse the fixture file."""
        # Check file exists
        if not self.filepath.exists():
            self.error_message = f"File not found: {self.filepath}"
            return

        # Check file size
        file_size = self.filepath.stat().st_size
        if file_size == 0:
            self.error_message = f"File is empty: {self.filepath}"
            return

        if file_size < 8:
            self.error_message = f"File too small ({file_size} bytes): {self.filepath}"
            return

        try:
            with open(self.filepath, "rb") as f:
                self.raw_data = f.read()
        except IOError as e:
            self.error_message = f"Failed to read file: {e}"
            return

        self.format_type = detect_format(self.raw_data)

        if self.format_type == "protobuf":
            self._load_protobuf()
        elif self.format_type == "flatbuffers":
            self._load_flatbuffers()
        else:
            # Try both formats
            if not self._load_protobuf():
                if not self._load_flatbuffers():
                    self.error_message = (
                        f"Unable to parse fixture: {self.filepath}\n"
                        f"  File size: {file_size} bytes\n"
                        f"  First 16 bytes (hex): {self.raw_data[:16].hex()}\n"
                        "  Not recognized as Protobuf or FlatBuffers format."
                    )

    def _load_protobuf(self) -> bool:
        """Try to load as Protobuf."""
        try:
            self.pb_fixture = elf_pb.ELFLoaderFixture()
            self.pb_fixture.ParseFromString(self.raw_data)
            self.format_type = "protobuf"
            self.error_message = None
            return True
        except DecodeError as e:
            self.pb_fixture = None
            # Don't set error_message here - let caller try FlatBuffers
            return False

    def _load_flatbuffers(self) -> bool:
        """Try to load as FlatBuffers and convert to Protobuf."""
        if not FLATBUFFERS_AVAILABLE:
            self.error_message = (
                "FlatBuffers support not available.\n"
                "  To install package: pip install flatbuffers>=24.0.0\n"
                "  To generate bindings: ./generate_flatbuffers.sh"
            )
            if _FB_IMPORT_ERROR:
                self.error_message += f"\n  Import error: {_FB_IMPORT_ERROR}"
            return False

        fb_fixture = parse_fb_elf_fixture(self.raw_data)
        if fb_fixture is None:
            self.error_message = f"Failed to parse FlatBuffers fixture: {self.filepath}"
            return False

        self.pb_fixture, convert_error = convert_fb_to_pb_elf_fixture(fb_fixture)
        if self.pb_fixture:
            self.format_type = "flatbuffers"
            self.error_message = None
            return True

        self.error_message = f"Failed to convert FlatBuffers to Protobuf: {self.filepath}\n  {convert_error}"
        return False

    @property
    def is_valid(self) -> bool:
        """Check if the fixture was loaded successfully."""
        return self.pb_fixture is not None

    @property
    def metadata(self):
        """Get fixture metadata."""
        if self.pb_fixture:
            return self.pb_fixture.metadata
        return None

    @property
    def input(self):
        """Get fixture input (ELFLoaderCtx)."""
        if self.pb_fixture:
            return self.pb_fixture.input
        return None

    @property
    def output(self):
        """Get fixture output (ELFLoaderEffects)."""
        if self.pb_fixture:
            return self.pb_fixture.output
        return None

    @property
    def fn_entrypoint(self) -> Optional[str]:
        """Get the function entrypoint from metadata."""
        if self.metadata:
            return self.metadata.fn_entrypoint
        return None

    @property
    def elf_data(self) -> bytes:
        """Get the ELF binary data."""
        if self.input and self.input.elf:
            return self.input.elf.data
        return b""

    def serialize_protobuf(self) -> bytes:
        """Serialize the fixture to Protobuf format."""
        if self.pb_fixture:
            return self.pb_fixture.SerializeToString()
        return b""

    def save_as_protobuf(self, output_path: Path) -> bool:
        """
        Save the fixture in Protobuf format.

        Args:
            output_path: Path to write the Protobuf file

        Returns:
            True if successful, False otherwise
        """
        if not self.pb_fixture:
            return False

        with open(output_path, "wb") as f:
            f.write(self.pb_fixture.SerializeToString())
        return True


def load_fixture_file(filepath: Path) -> Tuple[str, Optional[elf_pb.ELFLoaderFixture]]:
    """
    Load a fixture file, automatically detecting format and converting if needed.

    This is the main entry point for loading fixtures.

    Args:
        filepath: Path to the fixture file

    Returns:
        Tuple of (format_type, protobuf_fixture)
        format_type is 'flatbuffers', 'protobuf', or 'unknown'
        protobuf_fixture is the parsed/converted fixture or None if parsing failed
    """
    loader = FixtureLoader(filepath)
    return (loader.format_type, loader.pb_fixture)


def convert_file_to_protobuf(
    input_path: Path, output_path: Optional[Path] = None
) -> bool:
    """
    Convert a fixture file (FlatBuffers or Protobuf) to Protobuf format.

    Args:
        input_path: Path to the input file
        output_path: Path to write the Protobuf file (default: same name with .pb extension)

    Returns:
        True if conversion succeeded, False otherwise
    """
    if output_path is None:
        output_path = input_path.with_suffix(".pb")

    loader = FixtureLoader(input_path)

    if not loader.is_valid:
        print(f"Failed to load fixture from {input_path}")
        return False

    if loader.save_as_protobuf(output_path):
        print(
            f"Converted {input_path} ({loader.format_type}) to {output_path} (protobuf)"
        )
        return True
    return False


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="FlatBuffers/Protobuf fixture utilities"
    )
    parser.add_argument("input", type=Path, help="Input fixture file")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output file (for conversion)"
    )
    parser.add_argument("--detect", action="store_true", help="Only detect format")
    parser.add_argument("--convert", action="store_true", help="Convert to Protobuf")
    parser.add_argument("--info", action="store_true", help="Show fixture info")

    args = parser.parse_args()

    if args.detect:
        with open(args.input, "rb") as f:
            data = f.read()
        fmt = detect_format(data)
        print(f"Format: {fmt}")
        sys.exit(0)

    loader = FixtureLoader(args.input)

    if args.info or not args.convert:
        print(f"File: {args.input}")
        print(f"Format: {loader.format_type}")
        print(f"Valid: {loader.is_valid}")
        if loader.is_valid:
            print(f"  fn_entrypoint: {loader.fn_entrypoint}")
            print(f"  elf_size: {len(loader.elf_data)} bytes")
            if loader.output:
                print(f"  error: {loader.output.error}")

    if args.convert:
        output = args.output or args.input.with_suffix(".pb")
        if loader.save_as_protobuf(output):
            print(f"Saved to {output}")
        else:
            print("Conversion failed")
            sys.exit(1)
