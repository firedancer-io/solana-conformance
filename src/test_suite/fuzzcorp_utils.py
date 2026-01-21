import functools
import httpx
import typer
import time
import traceback
import random
from typing import Callable, TypeVar, Any
from test_suite.fuzzcorp_auth import get_fuzzcorp_auth, FuzzCorpAuth
from test_suite.fuzzcorp_api_client import FuzzCorpAPIClient

T = TypeVar("T")


def with_fuzzcorp_client(
    interactive: bool = True,
    max_retries: int = 1,
    show_errors: bool = True,
    backoff_base: float = 1.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            auth = get_fuzzcorp_auth(interactive=interactive)
            if not auth:
                if show_errors:
                    print("[ERROR] Failed to authenticate with FuzzCorp API")
                raise typer.Exit(code=1)

            def api_call_with_client(client: FuzzCorpAPIClient):
                kwargs["client"] = client
                return func(*args, **kwargs)

            return fuzzcorp_api_call(
                auth,
                api_call_with_client,
                interactive=interactive,
                max_retries=max_retries,
                show_errors=show_errors,
                backoff_base=backoff_base,
                backoff_max=backoff_max,
                jitter=jitter,
            )

        return wrapper

    return decorator


def fuzzcorp_api_call(
    auth: FuzzCorpAuth,
    api_func: Callable[[FuzzCorpAPIClient], T],
    interactive: bool = True,
    max_retries: int = 1,
    show_errors: bool = True,
    backoff_base: float = 1.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
) -> T:
    attempts = 0
    last_error = None

    while attempts <= max_retries:
        attempts += 1

        try:
            with FuzzCorpAPIClient(
                api_origin=auth.get_api_origin(),
                token=auth.get_token(),
                org=auth.get_organization(),
                project=auth.get_project(),
                http2=True,
            ) as client:
                result = api_func(client)
                return result
        except httpx.HTTPStatusError as e:
            last_error = e
            # Unauthorized / token expired
            if (
                e.response.status_code == 401
                and interactive
                and attempts <= max_retries
            ):
                if show_errors:
                    print("\n[INFO] Session expired. Re-authenticating...")
                auth.clear_token()
                if not auth.ensure_authenticated():
                    if show_errors:
                        print("[ERROR] Re-authentication failed")
                    raise typer.Exit(code=1)
                continue  # retry with new token (no backoff for auth)
            else:
                # Other HTTP errors
                is_retryable = _is_retryable_status(e.response.status_code)
                if is_retryable and attempts <= max_retries:
                    delay = _calculate_backoff(
                        attempts, backoff_base, backoff_max, jitter
                    )
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
    return status_code in (408, 429, 500, 502, 503, 504)


def _calculate_backoff(
    attempt: int, base: float, max_delay: float, use_jitter: bool
) -> float:
    # Capped exponential backoff: base * 2^(attempt-1)
    delay = min(base * (2 ** (attempt - 1)), max_delay)
    if use_jitter:
        jitter_amount = delay * 0.1 * random.random()
        delay += jitter_amount
    return delay
