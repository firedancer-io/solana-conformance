import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Callable, List, Any
import httpx
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
import tqdm


def run_fuzz_command(
    cmd: list[str], check: bool = True, stream_output: bool = False
) -> Optional[subprocess.CompletedProcess]:
    """
    Run a fuzz CLI command with consistent error handling.

    Args:
        cmd: Command list to execute (e.g., [fuzz_bin, "list", "repros", "--json"])
        check: If True, raises an error on non-zero exit code (default: True)
        stream_output: If True, stream stdout/stderr to terminal in real-time (default: False)

    Returns:
        CompletedProcess object on success, None on error
    """
    try:
        if stream_output:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )
            output_lines = []
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)
            returncode = process.wait()
            captured_output = "".join(output_lines)
            result = subprocess.CompletedProcess(
                args=cmd, returncode=returncode, stdout=captured_output, stderr=None
            )
            if check and returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode, cmd, captured_output, None
                )
            return result
        else:
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


def process_items(
    items: List[Any],
    process_func: Callable,
    num_processes: int = 4,
    debug_mode: bool = False,
    initializer: Optional[Callable] = None,
    initargs: tuple = (),
    desc: str = "Processing",
    use_processes: bool = False,
) -> List[Any]:
    results = []
    if debug_mode:
        num_processes = 1

    if num_processes > 1 or use_processes:
        if use_processes:
            executor = ProcessPoolExecutor(
                max_workers=num_processes, initializer=initializer, initargs=initargs
            )
        else:
            executor = ThreadPoolExecutor(max_workers=num_processes)
            if initializer:
                initializer(*initargs)
        try:
            with executor:
                future_to_item = {
                    executor.submit(process_func, item): item for item in items
                }

                with tqdm.tqdm(total=len(items), desc=desc) as pbar:
                    for future in as_completed(future_to_item):
                        result = future.result()
                        results.append(result)
                        pbar.update(1)
        except BrokenProcessPool as e:
            if not debug_mode:
                print(f"[ERROR] Process pool broken: {e}")
                raise
            else:
                # We assume a gdb/lldb session caused the pool to break; continue silently
                print(
                    f"[NOTICE] Process pool broken in debug mode. Silently continuing..."
                )
    else:
        for item in tqdm.tqdm(items, desc=desc):
            result = process_func(item)
            results.append(result)
    return results


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


def _request_with_retries(
    url: str,
    cookies: Optional[Dict[str, str]] = None,
    retries: int = 3,
    backoff: int = 2,
    stream: bool = False,
    raise_on_error: bool = False,
) -> Optional[httpx.Response]:
    """
    Internal function to make HTTP requests with retry logic.

    Args:
        url: URL to fetch
        cookies: Optional dictionary of cookies (e.g., {"s": "session_token"})
        retries: Number of retry attempts
        backoff: Exponential backoff factor for retries
        stream: Whether to stream the response
        raise_on_error: If True, raise RuntimeError on failure; if False, return None

    Returns:
        Response object on success, None on error (if raise_on_error=False)

    Raises:
        RuntimeError: If request fails and raise_on_error=True
    """
    for attempt in range(1, retries + 1):
        client = None
        try:
            client = httpx.Client(http2=True)
            if stream:
                # For streaming, we need to enter the context manager and return the response
                stream_context = client.stream("GET", url, cookies=cookies, timeout=30)
                response = stream_context.__enter__()
                response.raise_for_status()
                # Return both the response and context so it can be properly closed later
                response._httpx_stream_context = stream_context
                response._httpx_client = client
                return response
            else:
                response = client.get(url, cookies=cookies, timeout=30)
                response.raise_for_status()
                client.close()
                return response
        except httpx.HTTPStatusError as e:
            if client:
                client.close()
            # Authentication/authorization errors: don't retry
            if e.response is not None and e.response.status_code in [401, 403, 464]:
                print(f"[ERROR] Authentication/authorization failed for {url}")
                print(f"Status code: {e.response.status_code}")
                print(
                    f"Hint: Check that FUZZCORP_COOKIE environment variable is set correctly"
                )
                if raise_on_error:
                    raise RuntimeError(
                        f"Authentication failed for {url} (status {e.response.status_code})"
                    ) from e
                return None
            # Other HTTP errors: retry
            if attempt < retries:
                sleep_time = backoff ** (attempt - 1)
                print(f"[WARNING] HTTP error (attempt {attempt}/{retries}): {e}")
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                error_msg = f"Failed to fetch {url} after {retries} attempts"
                print(f"[ERROR] {error_msg}")
                print(f"Error: {e}")
                if raise_on_error:
                    raise RuntimeError(error_msg) from e
                return None
        except (httpx.RequestError, httpx.TimeoutException) as e:
            if client:
                client.close()
            # Network errors, timeouts, etc: retry
            if attempt < retries:
                sleep_time = backoff ** (attempt - 1)
                print(f"[WARNING] Request failed (attempt {attempt}/{retries}): {e}")
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                error_msg = f"Failed to fetch {url} after {retries} attempts"
                print(f"[ERROR] {error_msg}")
                print(f"Error: {e}")
                if raise_on_error:
                    raise RuntimeError(error_msg) from e
                return None


def fetch_with_retries(
    url: str,
    cookies: Optional[Dict[str, str]] = None,
    retries: int = 3,
    backoff: int = 2,
) -> Optional[str]:
    """
    Fetch content from a URL with retry logic and return as string.

    Args:
        url: URL to fetch
        cookies: Optional dictionary of cookies (e.g., {"s": "session_token"})
        retries: Number of retry attempts
        backoff: Exponential backoff factor for retries

    Returns:
        Response text on success, None on error
    """
    response = _request_with_retries(
        url,
        cookies=cookies,
        retries=retries,
        backoff=backoff,
        stream=False,
        raise_on_error=False,
    )
    return response.text if response else None


def download_with_retries(
    url: str,
    dest_path: Path,
    cookies: Optional[Dict[str, str]] = None,
    retries: int = 3,
    backoff: int = 2,
):
    """
    Download a file from a URL with retry logic.

    Args:
        url: URL to download from
        dest_path: Path to save the downloaded file
        cookies: Optional dictionary of cookies (e.g., {"s": "session_token"})
        retries: Number of retry attempts
        backoff: Exponential backoff factor for retries

    Raises:
        RuntimeError: If download fails after all retries
    """
    response = _request_with_retries(
        url,
        cookies=cookies,
        retries=retries,
        backoff=backoff,
        stream=True,
        raise_on_error=True,
    )
    if response:
        try:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        finally:
            # Close the streaming response and context
            if hasattr(response, "_httpx_stream_context"):
                response._httpx_stream_context.__exit__(None, None, None)
            if hasattr(response, "_httpx_client"):
                response._httpx_client.close()
