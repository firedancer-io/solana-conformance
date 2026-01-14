"""
Octane API utility functions for solana-conformance.

This module provides helper functions for making API calls to the Octane
orchestrator, similar to fuzzcorp_utils.py but for the Octane backend.
"""

import functools
import httpx
import typer
import time
import traceback
import random
from typing import Callable, TypeVar, Any, Optional
from test_suite.octane_api_client import OctaneAPIClient, DEFAULT_OCTANE_API_ORIGIN


T = TypeVar("T")


def get_octane_api_origin() -> str:
    """
    Get the Octane API origin URL.

    Checks environment variables in order:
    1. OCTANE_API_ORIGIN
    2. Falls back to default: gusc1b-fdfuzz-orchestrator1.jumpisolated.com:5000

    Returns:
        Octane API origin URL.
    """
    import os

    return os.getenv("OCTANE_API_ORIGIN", DEFAULT_OCTANE_API_ORIGIN)


def get_octane_client(
    api_origin: Optional[str] = None,
    bundle_id: Optional[str] = None,
    timeout: float = 300.0,
) -> OctaneAPIClient:
    """
    Create an Octane API client.

    Args:
        api_origin: Optional API origin URL. Uses environment/default if not provided.
        bundle_id: Optional bundle ID to filter queries.
        timeout: Request timeout in seconds.

    Returns:
        Configured OctaneAPIClient instance.
    """
    return OctaneAPIClient(
        api_origin=api_origin or get_octane_api_origin(),
        bundle_id=bundle_id,
        timeout=timeout,
    )


def with_octane_client(
    max_retries: int = 3,
    show_errors: bool = True,
    backoff_base: float = 1.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
):
    """
    Decorator for functions that need an Octane API client.

    Automatically creates a client and handles retries with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        show_errors: Whether to print error messages.
        backoff_base: Base delay for exponential backoff.
        backoff_max: Maximum backoff delay.
        jitter: Whether to add jitter to backoff delays.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            def api_call_with_client(client: OctaneAPIClient):
                kwargs["client"] = client
                return func(*args, **kwargs)

            return octane_api_call(
                api_call_with_client,
                max_retries=max_retries,
                show_errors=show_errors,
                backoff_base=backoff_base,
                backoff_max=backoff_max,
                jitter=jitter,
            )

        return wrapper

    return decorator


def octane_api_call(
    api_func: Callable[[OctaneAPIClient], T],
    api_origin: Optional[str] = None,
    bundle_id: Optional[str] = None,
    max_retries: int = 3,
    show_errors: bool = True,
    backoff_base: float = 1.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
) -> T:
    """
    Make an API call to Octane with retry logic.

    Args:
        api_func: Function that takes an OctaneAPIClient and returns a result.
        api_origin: Optional API origin URL.
        bundle_id: Optional bundle ID.
        max_retries: Maximum number of retry attempts.
        show_errors: Whether to print error messages.
        backoff_base: Base delay for exponential backoff.
        backoff_max: Maximum backoff delay.
        jitter: Whether to add jitter to backoff delays.

    Returns:
        Result of api_func.

    Raises:
        typer.Exit: If all retries are exhausted.
    """
    attempts = 0
    last_error = None

    while attempts <= max_retries:
        attempts += 1

        try:
            with OctaneAPIClient(
                api_origin=api_origin or get_octane_api_origin(),
                bundle_id=bundle_id,
                http2=True,
            ) as client:
                result = api_func(client)
                return result
        except httpx.HTTPStatusError as e:
            last_error = e
            is_retryable = _is_retryable_status(e.response.status_code)
            if is_retryable and attempts <= max_retries:
                delay = _calculate_backoff(attempts, backoff_base, backoff_max, jitter)
                if show_errors:
                    print(
                        f"[INFO] Request failed with {e.response.status_code}, "
                        f"retrying in {delay:.1f}s (attempt {attempts}/{max_retries + 1})..."
                    )
                time.sleep(delay)
                continue
            else:
                if show_errors:
                    print(f"[ERROR] HTTP request failed: {e}")
                    if hasattr(e, "response") and e.response:
                        print(f"[ERROR] Response: {e.response.text}")
                raise typer.Exit(code=1)
        except httpx.HTTPError as e:
            # Network errors are retryable
            last_error = e
            if attempts <= max_retries:
                delay = _calculate_backoff(attempts, backoff_base, backoff_max, jitter)
                if show_errors:
                    print(
                        f"[INFO] Network error ({e}), "
                        f"retrying in {delay:.1f}s (attempt {attempts}/{max_retries + 1})..."
                    )
                time.sleep(delay)
                continue
            else:
                if show_errors:
                    print(f"[ERROR] HTTP request failed: {e}")
                    if hasattr(e, "response") and e.response:
                        print(f"[ERROR] Response: {e.response.text}")
                raise typer.Exit(code=1)
        except Exception as e:
            # Unexpected errors are not retryable
            last_error = e
            if show_errors:
                print(f"[ERROR] Request failed: {e}")
                traceback.print_exc()
            raise typer.Exit(code=1)

    # Out of remaining retries
    if show_errors and last_error:
        print(f"[ERROR] Failed after {max_retries + 1} attempts: {last_error}")
    raise typer.Exit(code=1)


def _is_retryable_status(status_code: int) -> bool:
    """Check if an HTTP status code is retryable."""
    return status_code in (408, 429, 500, 502, 503, 504)


def _calculate_backoff(
    attempt: int, base: float, max_delay: float, use_jitter: bool
) -> float:
    """Calculate exponential backoff delay with optional jitter."""
    # Capped exponential backoff: base * 2^(attempt-1)
    delay = min(base * (2 ** (attempt - 1)), max_delay)
    if use_jitter:
        jitter_amount = delay * 0.1 * random.random()
        delay += jitter_amount
    return delay


def validate_octane_connection(api_origin: Optional[str] = None) -> bool:
    """
    Validate that the Octane API is reachable.

    Args:
        api_origin: Optional API origin URL to test.

    Returns:
        True if the API is healthy, False otherwise.
    """
    try:
        with OctaneAPIClient(
            api_origin=api_origin or get_octane_api_origin(),
        ) as client:
            return client.health_check()
    except Exception:
        return False
