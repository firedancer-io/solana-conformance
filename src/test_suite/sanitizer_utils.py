"""
Sanitizer utilities for loading coverage-instrumented shared libraries.

This module handles the setup required to load .so files built with sanitizer
coverage instrumentation (e.g., -fsanitize-coverage) outside of a fuzzer harness.
"""

import ctypes
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import List, Optional, Tuple

# Thread-safe caches
_ASAN_LOOKUP_LOCK = threading.Lock()
_ASAN_PATH_CACHE: Optional[str] = None
_ASAN_LOOKUP_DONE = False

_SANCOV_STUB_LOCK = threading.Lock()
_SANCOV_STUB_PATH: Optional[str] = None
_SANCOV_STUB_CHECKED = False

# Sanitizer coverage stub source - provides dummy symbols for coverage-instrumented binaries
_SANCOV_STUB_SOURCE = """\
#include <stdint.h>
#include <stddef.h>

// Thread-local variable used by sanitizer coverage to track lowest stack address
// This must be exported for libraries built with -fsanitize-coverage=stack-depth
__thread uintptr_t __sancov_lowest_stack = 0;

void __sanitizer_cov_8bit_counters_init(uint8_t *start, uint8_t *stop) {}
void __sanitizer_cov_pcs_init(const uintptr_t *pcs_beg, const uintptr_t *pcs_end) {}
void __sanitizer_cov_trace_pc_guard_init(uint32_t *start, uint32_t *stop) {}
void __sanitizer_cov_trace_pc_guard(uint32_t *guard) {}
void __sanitizer_cov_trace_cmp1(uint8_t arg1, uint8_t arg2) {}
void __sanitizer_cov_trace_cmp2(uint16_t arg1, uint16_t arg2) {}
void __sanitizer_cov_trace_cmp4(uint32_t arg1, uint32_t arg2) {}
void __sanitizer_cov_trace_cmp8(uint64_t arg1, uint64_t arg2) {}
void __sanitizer_cov_trace_const_cmp1(uint8_t arg1, uint8_t arg2) {}
void __sanitizer_cov_trace_const_cmp2(uint16_t arg1, uint16_t arg2) {}
void __sanitizer_cov_trace_const_cmp4(uint32_t arg1, uint32_t arg2) {}
void __sanitizer_cov_trace_const_cmp8(uint64_t arg1, uint64_t arg2) {}
void __sanitizer_cov_trace_switch(uint64_t val, uint64_t *cases) {}
void __sanitizer_cov_trace_div4(uint32_t val) {}
void __sanitizer_cov_trace_div8(uint64_t val) {}
void __sanitizer_cov_trace_gep(uintptr_t idx) {}
void __sanitizer_cov_trace_pc(void) {}
void __sanitizer_cov_trace_pc_indir(uintptr_t callee) {}
"""


def locate_sancov_stub() -> Optional[str]:
    """
    Locate or build a sancov stub library that provides dummy sanitizer coverage symbols.

    This is needed when loading .so files built with -fsanitize-coverage but running
    outside of a fuzzer harness that would normally provide these symbols.

    Returns:
        Path to the sancov stub library, or None if it couldn't be found/built.
    """
    global _SANCOV_STUB_PATH, _SANCOV_STUB_CHECKED
    with _SANCOV_STUB_LOCK:
        if _SANCOV_STUB_CHECKED:
            return _SANCOV_STUB_PATH

        _SANCOV_STUB_CHECKED = True

        # First, check for clang's fuzzer runtime which provides these symbols
        try:
            out = subprocess.run(
                ["ldconfig", "-p"],
                check=False,
                capture_output=True,
                text=True,
            )
            if out.returncode == 0 and out.stdout:
                for line in out.stdout.splitlines():
                    # Look for libFuzzer runtime or sancov standalone
                    if (
                        "libclang_rt.fuzzer" in line or "libclang_rt.sancov" in line
                    ) and "=>" in line:
                        candidate = line.strip().split()[-1]
                        if os.path.isfile(candidate):
                            _SANCOV_STUB_PATH = candidate
                            return _SANCOV_STUB_PATH
        except Exception:
            pass

        # Build a stub library in a temp location
        stub_dir = Path(tempfile.gettempdir()) / "solana_conformance_sancov_stub"
        stub_so = stub_dir / "libsancov_stub.so"
        stub_c = stub_dir / "sancov_stub.c"

        # Check if we already built it
        if stub_so.exists():
            _SANCOV_STUB_PATH = str(stub_so)
            return _SANCOV_STUB_PATH

        # Try to build it
        try:
            stub_dir.mkdir(parents=True, exist_ok=True)
            stub_c.write_text(_SANCOV_STUB_SOURCE)

            # Try gcc first, then clang
            for compiler in ("gcc", "clang"):
                compiler_path = shutil.which(compiler)
                if compiler_path:
                    result = subprocess.run(
                        [
                            compiler_path,
                            "-shared",
                            "-fPIC",
                            "-o",
                            str(stub_so),
                            str(stub_c),
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0 and stub_so.exists():
                        _SANCOV_STUB_PATH = str(stub_so)
                        print(f"Built sancov stub library: {_SANCOV_STUB_PATH}")
                        return _SANCOV_STUB_PATH
        except Exception as e:
            print(f"Warning: Failed to build sancov stub library: {e}")

        return None


def locate_asan_library() -> Optional[str]:
    """
    Locate libasan on the system (cached).

    Returns:
        Path to libasan shared library, or None if not found.
    """
    global _ASAN_PATH_CACHE, _ASAN_LOOKUP_DONE
    with _ASAN_LOOKUP_LOCK:
        if _ASAN_LOOKUP_DONE:
            return _ASAN_PATH_CACHE

        asan_path: Optional[str] = None
        try:
            out = subprocess.run(
                ["ldconfig", "-p"],
                check=False,
                capture_output=True,
                text=True,
            )
            if out.returncode == 0 and out.stdout:
                for line in out.stdout.splitlines():
                    if "libasan.so" in line and "=>" in line:
                        candidate = line.strip().split()[-1]
                        if os.path.isfile(candidate):
                            asan_path = candidate
                            break
        except Exception:
            pass

        if not asan_path:
            for candidate in (
                "/lib64/libasan.so.8",
                "/usr/lib64/libasan.so.8",
                "/lib64/libasan.so.6",
                "/usr/lib64/libasan.so.6",
            ):
                if os.path.isfile(candidate):
                    asan_path = candidate
                    break

        _ASAN_PATH_CACHE = asan_path
        _ASAN_LOOKUP_DONE = True
        return asan_path


def build_ld_preload(
    asan_path: Optional[str],
    sancov_path: Optional[str],
    existing: Optional[str] = None,
    target_libraries: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Build LD_PRELOAD string with sanitizer libraries and target libraries.

    Args:
        asan_path: Path to ASAN library (or None)
        sancov_path: Path to sancov stub library (or None)
        existing: Existing LD_PRELOAD value to append to
        target_libraries: List of target .so files to preload (avoids TLS errors)

    Returns:
        Combined LD_PRELOAD string or None if no libraries to preload
    """
    parts = []
    # Sancov stub MUST be first - it provides __sancov_lowest_stack which is
    # needed by target libraries built with -sanitizer-coverage-stack-depth.
    # When sanitizers spawn llvm-symbolizer, it inherits LD_PRELOAD and needs
    # to resolve this symbol before loading the instrumented target libraries.
    if sancov_path:
        parts.append(sancov_path)
    # Target libraries next - they need TLS allocated at startup to avoid
    # "cannot allocate memory in static TLS block" errors
    if target_libraries:
        for lib in target_libraries:
            if lib and os.path.isfile(str(lib)):
                parts.append(str(lib))
    if asan_path:
        parts.append(asan_path)

    if not parts:
        return existing

    result = ":".join(parts)
    if existing:
        result = f"{result}:{existing}"
    return result


def setup_sanitizer_environment(
    target_libraries: Optional[List[str]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Set up the environment for loading sanitizer-instrumented shared libraries.

    This function:
    1. Locates ASAN library and configures ASAN_OPTIONS
    2. Locates or builds sancov stub library
    3. Sets LD_PRELOAD with all required libraries
    4. Preloads the sancov stub into the current process

    Args:
        target_libraries: List of target .so files to include in LD_PRELOAD

    Returns:
        Tuple of (asan_path, sancov_path) for reference
    """
    # Locate libraries
    asan_path = locate_asan_library()
    sancov_path = locate_sancov_stub()

    # Configure ASAN options
    existing_asan_opts = os.environ.get("ASAN_OPTIONS", "")
    required_opts = ["detect_leaks=0", "verify_asan_link_order=0"]

    opts_list = [opt for opt in existing_asan_opts.split(":") if opt]
    for opt in required_opts:
        if opt not in opts_list:
            opts_list.insert(0, opt)

    os.environ["ASAN_OPTIONS"] = ":".join(opts_list)

    # Build and set LD_PRELOAD
    ld_preload = build_ld_preload(
        asan_path,
        sancov_path,
        os.environ.get("LD_PRELOAD"),
        target_libraries=target_libraries,
    )
    if ld_preload:
        os.environ["LD_PRELOAD"] = ld_preload

    # Preload sancov stub into current process (provides symbols globally)
    if sancov_path:
        try:
            ctypes.CDLL(sancov_path, mode=ctypes.RTLD_GLOBAL)
        except Exception as e:
            print(f"Warning: Failed to preload sancov stub: {e}")

    return asan_path, sancov_path


def load_shared_library_safe(
    library_path: str,
    target_libraries: Optional[List[str]] = None,
) -> ctypes.CDLL:
    """
    Safely load a shared library, setting up sanitizer environment if needed.

    This function attempts to load the library, and if it fails due to missing
    sanitizer symbols, it sets up the sanitizer environment and retries.

    Args:
        library_path: Path to the .so file to load
        target_libraries: Additional target libraries to preload

    Returns:
        Loaded CDLL object

    Raises:
        OSError: If the library cannot be loaded even after setup
    """
    # First try: attempt direct load
    try:
        return ctypes.CDLL(library_path)
    except OSError as e:
        error_msg = str(e)

        # Check if this is a sanitizer symbol error
        sancov_patterns = [
            "__sanitizer_cov_",
            "sanitizer_cov_8bit",
            "sanitizer_cov_pcs",
            "sanitizer_cov_trace",
        ]

        is_sancov_error = any(pattern in error_msg for pattern in sancov_patterns)

        if not is_sancov_error:
            # Not a sanitizer error, re-raise
            raise

        # Set up sanitizer environment
        all_targets = list(target_libraries) if target_libraries else []
        if library_path not in all_targets:
            all_targets.append(library_path)

        print(
            f"Library has missing sanitizer coverage symbols, setting up environment..."
        )
        setup_sanitizer_environment(target_libraries=all_targets)

        # Retry load
        return ctypes.CDLL(library_path)
