import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import getpass
import httpx
from test_suite.fuzzcorp_api_client import USER_DATA_PATH, SESSION_COOKIE, LOGIN_PATH
import urllib.parse


class FuzzCorpAuth:
    DEFAULT_CONFIG_FILE = Path.home() / ".fuzzcorp_token"

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"[WARNING] Failed to load token cache from {self.config_file}: {e}"
                )
                self.config = {}

    def _save_config(self):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            os.chmod(self.config_file, 0o600)
        except IOError as e:
            print(f"[WARNING] Failed to save token cache to {self.config_file}: {e}")

    def get_api_origin(self) -> Optional[str]:
        return os.getenv("FUZZ_API_ORIGIN")

    def get_organization(self) -> Optional[str]:
        return os.getenv("FUZZ_ORGANIZATION")

    def get_project(self) -> Optional[str]:
        return os.getenv("FUZZ_PROJECT")

    def get_missing_config(self) -> list[str]:
        """Return list of missing required environment variables."""
        missing = []
        if not self.get_api_origin():
            missing.append("FUZZ_API_ORIGIN")
        if not self.get_organization():
            missing.append("FUZZ_ORGANIZATION")
        if not self.get_project():
            missing.append("FUZZ_PROJECT")
        return missing

    def print_missing_config_error(self, missing_config: list[str]) -> None:
        print()
        print("[ERROR] Required FuzzCorp configuration not set:")
        for var in missing_config:
            print(f"  - {var}")
        print("\nPlease set these environment variables:")
        print("  export FUZZ_API_ORIGIN='https://your-fuzzcorp-instance.com'")
        print("  export FUZZ_ORGANIZATION='your-organization'")
        print("  export FUZZ_PROJECT='your-project'")
        print("\nContact your FuzzCorp administrator for the correct values.")

    def get_token(self) -> Optional[str]:
        return os.getenv("FUZZ_TOKEN") or self.config.get("token")

    def get_username(self) -> Optional[str]:
        return os.getenv("FUZZ_USERNAME") or self.config.get("username")

    def set_token(self, token: str, username: Optional[str] = None):
        self.config["token"] = token
        if username:
            self.config["username"] = username
        self._save_config()

    def set_config(
        self,
        token: Optional[str] = None,
        username: Optional[str] = None,
    ):
        if token:
            self.config["token"] = token
        if username:
            self.config["username"] = username

        self._save_config()

    def clear_token(self):
        if "token" in self.config:
            del self.config["token"]
            self._save_config()

    def clear_all(self):
        self.config = {}
        if self.config_file.exists():
            self.config_file.unlink()

    def is_authenticated(self) -> bool:
        has_token = self.get_token() is not None
        has_password = os.getenv("FUZZ_PASSWORD") is not None
        has_username = self.get_username() is not None

        return has_token or (has_username and has_password)

    def get_missing_auth(self) -> Optional[str]:
        if not self.is_authenticated():
            return "FUZZ_TOKEN or (FUZZ_USERNAME + FUZZ_PASSWORD)"
        return None

    def interactive_setup(self, force: bool = False) -> bool:
        print("\n" + "=" * 60)
        print("FuzzCorp API Authentication")
        print("=" * 60)

        # Check for missing required configuration
        missing_config = self.get_missing_config()
        if missing_config:
            self.print_missing_config_error(missing_config)
            return False

        print(f"\nAPI Origin: {self.get_api_origin()}")
        print(f"Organization: {self.get_organization()}")
        print(f"Project: {self.get_project()}\n")

        if not force and self.get_token():
            print("Authentication token already cached!")
            print("\nValidating token...")
            if self.validate_token():
                print("Token is valid!")
                print("\nTo re-authenticate, run with --force.")
                return True
            else:
                print("[ERROR] Cached token is invalid or expired")
                self.clear_token()

        print("-" * 60)
        print("Authentication Required")
        print("-" * 60)

        current_username = self.get_username()
        if current_username:
            print(f"\nPrevious username: {current_username}")

        username_prompt = (
            f"Username [{current_username}]: " if current_username else "Username: "
        )
        username = input(username_prompt).strip()
        if not username and current_username:
            username = current_username

        if not username:
            print("[ERROR] Username cannot be empty")
            return False

        password = getpass.getpass("Password (hidden): ").strip()
        if not password:
            print("[ERROR] Password cannot be empty")
            return False

        print("\nAuthenticating...")
        api_origin = self.get_api_origin()
        token = self._authenticate(api_origin, username, password)
        if not token:
            print("[ERROR] Authentication failed")
            return False

        print("Authentication successful!")
        self.set_token(token=token, username=username)

        print("\n" + "=" * 60)
        print("Token cached to:", self.config_file)
        print("=" * 60)
        print("\nSetup complete! You can now use the FuzzCorp API.\n")

        return True

    def _authenticate(
        self, api_origin: str, username: str, password: str
    ) -> Optional[str]:
        url = api_origin.rstrip("/") + LOGIN_PATH
        print(f"Authenticating with {api_origin}...")
        try:
            with httpx.Client(http2=True, timeout=30.0) as client:
                response = client.post(
                    url,
                    json={"usr": username, "pw": password},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()
                token = data.get("token")
                if not token:
                    for cookie in response.cookies.jar:
                        if cookie.name == SESSION_COOKIE:
                            return cookie.value
                return token
        except httpx.HTTPError as e:
            print(f"[ERROR] Authentication failed: {e}")
            if hasattr(e, "response") and e.response:
                try:
                    error_data = e.response.json()
                    if "error" in error_data:
                        print(f"[ERROR] {error_data['error']}")
                except:
                    print(f"[ERROR] {e.response.text}")
            return None
        except Exception as e:
            print(f"[ERROR] Authentication error: {e}")
            return None

    def validate_token(self) -> bool:
        token = self.get_token()
        if not token:
            return False

        api_origin = self.get_api_origin()
        if not api_origin:
            return False

        url = api_origin.rstrip("/") + USER_DATA_PATH

        try:
            with httpx.Client(http2=True, timeout=30.0) as client:
                parsed_url = urllib.parse.urlparse(api_origin)
                client.cookies.set(
                    SESSION_COOKIE,
                    token,
                    domain=parsed_url.hostname,
                    path="/",
                )
                response = client.get(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
                return True
        except (httpx.HTTPError, Exception):
            return False

    def ensure_authenticated(self) -> bool:
        if self.get_token() and self.validate_token():
            return True
        self.clear_token()

        username = self.get_username()
        api_origin = self.get_api_origin()

        if username and api_origin:
            print("\n[INFO] Session expired. Please re-authenticate.")
            password = getpass.getpass(f"FuzzCorp NG password for {username}: ").strip()

            if password:
                print("Authenticating...")
                token = self._authenticate(api_origin, username, password)
                if token:
                    self.set_config(token=token)
                    print("Authentication successful!")
                    return True
                else:
                    print("[ERROR] Authentication failed")

        print("\n[INFO] Authentication required. Please complete setup.")
        return self.interactive_setup(force=True)


def get_fuzzcorp_auth(interactive: bool = True) -> Optional[FuzzCorpAuth]:
    auth = FuzzCorpAuth()

    # Check for missing required configuration first
    missing_config = auth.get_missing_config()
    if missing_config:
        auth.print_missing_config_error(missing_config)
        return None

    if auth.is_authenticated():
        return auth

    if not interactive:
        missing_auth = auth.get_missing_auth()
        print("[ERROR] Authentication required but not configured.")
        print(f"Please set: {missing_auth}")
        print(
            "\nOr run with --interactive to authenticate, or use 'configure-fuzzcorp' command."
        )
        return None

    # Interactive setup
    if auth.interactive_setup():
        return auth
    return None
