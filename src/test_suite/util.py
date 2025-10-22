import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_fuzz_command(
    cmd: list[str], check: bool = True
) -> Optional[subprocess.CompletedProcess]:
    """
    Run a fuzz CLI command with consistent error handling.

    Args:
        cmd: Command list to execute (e.g., [fuzz_bin, "list", "repros", "--json"])
        check: If True, raises an error on non-zero exit code (default: True)

    Returns:
        CompletedProcess object on success, None on error
    """
    try:
        return subprocess.run(cmd, text=True, capture_output=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd)}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error running command: {' '.join(cmd)}")
        print(f"Error: {e}")
        return None


def deduplicate_fixtures_by_hash(directory: Path) -> int:
    """
    Removes duplicate files in the given directory based on content hash.
    Returns number of duplicates removed.
    """
    seen_hashes = {}
    num_duplicates = 0

    for file_path in Path(directory).iterdir():
        if not file_path.is_file():
            continue
        # Hash file contents
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).digest()

        if file_hash in seen_hashes:
            file_path.unlink()  # delete duplicate
            num_duplicates += 1
        else:
            seen_hashes[file_hash] = file_path

    return num_duplicates


def set_ld_preload_asan():
    # Run ldconfig -p and capture output
    ldconfig_output = subprocess.check_output(["ldconfig", "-p"], text=True)

    # Filter lines containing "asan"
    asan_libs = [line for line in ldconfig_output.split("\n") if "asan" in line]

    # Extract the first library path if available
    if asan_libs:
        first_asan_lib = asan_libs[0].split()[-1]
    else:
        print("No ASAN library found.")
        return

    # Set LD_PRELOAD environment variable
    os.environ["LD_PRELOAD"] = first_asan_lib
    print(f"LD_PRELOAD set to {first_asan_lib}")
    os.execvp(sys.argv[0], sys.argv)
