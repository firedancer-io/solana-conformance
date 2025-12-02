import json
import os
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
import httpx


# API Constants (from fuzzcorp-ng/ui/endpoints*.go)
API_PREFIX = "/api/"
PROTECTED_PREFIX = API_PREFIX + "protected/"
AUTH_PREFIX = API_PREFIX + "auth/"
STORAGE_PREFIX = PROTECTED_PREFIX + "storage/"
USER_PREFIX = PROTECTED_PREFIX + "user/"

# Endpoints
LOGIN_PATH = AUTH_PREFIX + "login"
USER_DATA_PATH = USER_PREFIX + "data"
REPRO_INDEX_PATH = STORAGE_PREFIX + "repro_index"
REPRO_LIST_PATH = STORAGE_PREFIX + "repro_list"
REPRO_BY_HASH_PATH = STORAGE_PREFIX + "repro_hash"
STORAGE_DATA_GET_PATH = STORAGE_PREFIX + "data_entry"

# Session cookie name
SESSION_COOKIE = "__Host-FuzzCorp_Session"


@dataclass
class LineageRepro:
    hash: str
    created_at: datetime
    count: int
    all_verified: bool
    # Optional extra metadata available on newer APIs
    drivers: Optional[List[str]] = None
    config_indices: Optional[List[int]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineageRepro":
        # Hash is required in all known schemas
        hash_value = data.get("Hash") or data.get("hash")
        if not hash_value:
            raise KeyError("Hash")

        # CreatedAt is present in both schemas, normalize if available
        created_at_str = data.get("CreatedAt") or data.get("created_at")
        if created_at_str:
            # Handle both RFC3339 formats
            if created_at_str.endswith("Z"):
                created_at_str = created_at_str[:-1] + "+00:00"
            created_at = datetime.fromisoformat(created_at_str)
        else:
            # Fallback to a stable value so sorting still works
            created_at = datetime.min

        # Count:
        # - prefer explicit Count from legacy schema
        # - otherwise derive from ConfigIndices (one count per config index)
        # - final fallback is a single repro
        if "Count" in data:
            count = int(data["Count"])
        else:
            cfg_indices = data.get("ConfigIndices") or data.get("config_indices") or []
            if isinstance(cfg_indices, list):
                count = max(len(cfg_indices), 1) if cfg_indices else 1
            else:
                # Unexpected shape: treat as a single repro
                count = 1

        # AllVerified:
        # - legacy AllVerified flag if present
        # - otherwise fall back to the newer Verified flag
        if "AllVerified" in data:
            all_verified = bool(data["AllVerified"])
        else:
            all_verified = bool(data.get("Verified") or data.get("verified") or False)

        drivers = data.get("Drivers") or data.get("drivers")
        cfg_indices_val = data.get("ConfigIndices") or data.get("config_indices")

        return cls(
            hash=hash_value,
            created_at=created_at,
            count=count,
            all_verified=all_verified,
            drivers=drivers,
            config_indices=cfg_indices_val,
        )


@dataclass
class ReproIndexResponse:
    bundle_id: str
    lineages: Dict[str, List[LineageRepro]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReproIndexResponse":
        lineages = {}
        # Support both legacy "Lineages" and potential future "lineages"
        lineages_data = data.get("Lineages") or data.get("lineages") or {}
        for lineage_name, repros in lineages_data.items():
            lineages[lineage_name] = [LineageRepro.from_dict(r) for r in (repros or [])]

        # Bundle ID:
        # - legacy compat: top-level "BundleID"
        # - current NG API: "Bundle" object with "id" field
        bundle_id = data.get("BundleID")
        if not bundle_id:
            bundle = data.get("Bundle") or data.get("bundle")
            if isinstance(bundle, dict):
                bundle_id = bundle.get("id") or bundle.get("ID")
        if not bundle_id:
            bundle_id = data.get("bundle_id", "00000000-0000-0000-0000-000000000000")

        return cls(bundle_id=bundle_id, lineages=lineages)


@dataclass
class ReproMetadata:
    hash: str
    bundle: str
    lineage: str
    asset: Optional[str]
    artifact_hashes: List[str]
    summary: str
    flaky: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReproMetadata":
        if "repros" in data and isinstance(data["repros"], dict):
            inner = data["repros"]
        else:
            inner = data

        # Core identifiers
        hash_val = inner.get("hash") or inner.get("Hash")
        if not hash_val:
            raise KeyError("hash")

        bundle_val = inner.get("bundle") or inner.get("Bundle")
        lineage_val = inner.get("lineage") or inner.get("Lineage")
        asset_val = inner.get("asset") or inner.get("Asset")

        # Artifact hashes:
        artifact_hashes_val: List[str]
        raw_hashes = inner.get("artifact_hashes")
        if raw_hashes:
            artifact_hashes_val = list(raw_hashes)
        else:
            single_hash = inner.get("artifact_hash") or inner.get("ArtifactHash")
            if single_hash:
                artifact_hashes_val = [single_hash]
            else:
                artifact_hashes_val = []

        return cls(
            hash=hash_val,
            bundle=str(bundle_val) if bundle_val is not None else "",
            lineage=lineage_val or "",
            asset=asset_val,
            artifact_hashes=artifact_hashes_val,
            summary=inner.get("summary") or "",
            flaky=bool(inner.get("flaky", False)),
        )


class FuzzCorpAPIClient:
    def __init__(
        self,
        api_origin: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        org: Optional[str] = None,
        project: Optional[str] = None,
        verify_ssl: bool = True,
        http2: bool = True,
        timeout: float = 300.0,
    ):
        self.api_origin = api_origin.rstrip("/")
        self.org = org or os.getenv("FUZZCORP_ORG")
        self.project = project or os.getenv("FUZZCORP_PROJECT")

        self.client = httpx.Client(
            verify=verify_ssl,
            http2=http2,
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

        if token:
            self._set_token(token)
        elif username and password:
            self.login(username, password)
        else:
            raise ValueError("Must provide either (username, password) or token")

    def _set_token(self, token: str):
        from http.cookiejar import Cookie

        parsed_url = urllib.parse.urlparse(self.api_origin)
        is_https = parsed_url.scheme == "https"

        cookie = Cookie(
            version=0,
            name=SESSION_COOKIE,
            value=token,
            port=None,
            port_specified=False,
            domain=parsed_url.hostname,
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=is_https,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        self.client.cookies.jar.set_cookie(cookie)

    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        use_query: bool = False,
    ) -> Dict[str, Any]:
        url = self.api_origin + path

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if method.upper() == "GET" and data and use_query:
            # arpc protocol: encode data as JSON in query parameter
            query_data = json.dumps(data)
            url = f"{url}?arpc={urllib.parse.quote(query_data)}"
            response = self.client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = self.client.post(url, json=data, headers=headers)
        elif method.upper() == "GET":
            # GET without query encoding (for simple requests)
            response = self.client.get(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    def login(self, username: str, password: str) -> str:
        data = {
            "usr": username,
            "pw": password,
        }

        response = self._make_request("POST", LOGIN_PATH, data)
        token = response.get("token")

        if not token:
            for cookie in self.client.cookies.jar:
                if cookie.name == SESSION_COOKIE:
                    return cookie.value
            raise ValueError("Login response did not contain a token")

        self._set_token(token)
        return token

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def list_repros(
        self,
        bundle_id: Optional[str] = None,
        org: Optional[str] = None,
        project: Optional[str] = None,
    ) -> ReproIndexResponse:
        data = {
            "org": org or self.org,
            "prj": project or self.project,
            "BundleID": bundle_id or "00000000-0000-0000-0000-000000000000",
        }

        response = self._make_request("GET", REPRO_INDEX_PATH, data, use_query=True)
        return ReproIndexResponse.from_dict(response)

    def list_repros_full(
        self,
        bundle_id: Optional[str] = None,
        org: Optional[str] = None,
        project: Optional[str] = None,
        lineage: Optional[str] = None,
    ) -> List[ReproMetadata]:
        data = {
            "org": org or self.org,
            "prj": project or self.project,
            "BundleID": bundle_id or "00000000-0000-0000-0000-000000000000",
        }

        # Add lineage filter if provided (filters server-side for efficiency)
        if lineage:
            data["Lineage"] = lineage

        response = self._make_request("GET", REPRO_LIST_PATH, data, use_query=True)
        repros = response.get("repros") or []
        return [ReproMetadata.from_dict(repro) for repro in repros]

    def get_repro_by_hash(
        self,
        repro_hash: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
    ) -> ReproMetadata:
        data = {
            "Hash": repro_hash,
            "org": org or self.org,
            "prj": project or self.project,
        }

        response = self._make_request("GET", REPRO_BY_HASH_PATH, data, use_query=True)
        if not response:
            raise ValueError(f"No repro found for hash: {repro_hash}")
        return ReproMetadata.from_dict(response)

    def _download_with_progress(
        self,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
        update_shared_progress: bool = True,
    ) -> bytes:
        url = self.api_origin + STORAGE_DATA_GET_PATH
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/octet-stream",
        }

        # Encode data as arpc query parameter
        query_data = json.dumps(data)
        url = f"{url}?arpc={urllib.parse.quote(query_data)}"

        # Stream the response to handle large files
        with self.client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()

            # Get content length from header if available
            content_length = response.headers.get("Content-Length")
            total_size = int(content_length) if content_length else None

            # Download with progress tracking
            # Note: We don't create a progress bar here to avoid nesting with
            # top-level tqdm progress bars from process_items() in util.py
            chunks = []
            downloaded = 0

            for chunk in response.iter_bytes(chunk_size=8192):
                if chunk:
                    chunk_size_bytes = len(chunk)
                    chunks.append(chunk)
                    downloaded += chunk_size_bytes

                    # Update shared progress bar if available (thread-safe)
                    if update_shared_progress:
                        try:
                            import test_suite.globals as globals

                            if globals.download_progress_bar is not None:
                                globals.download_progress_bar.update(chunk_size_bytes)
                        except:
                            pass  # Silently continue if progress bar not available

                    # Call progress callback if provided
                    if progress_callback and total_size:
                        progress_callback(downloaded, total_size)

            return b"".join(chunks)

    def download_artifact_data(
        self,
        artifact_hash: str,
        lineage: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        data = {
            "file_name": artifact_hash,
            "kind": "artifact",
            "organization": org or self.org,
            "project": project or self.project,
            "lineage": lineage,
        }

        return self._download_with_progress(
            data=data,
            progress_callback=progress_callback,
            desc=desc or f"Downloading {artifact_hash[:8]}",
        )

    def download_repro_data(
        self,
        repro_hash: str,
        lineage: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        data = {
            "file_name": repro_hash,
            "kind": "repro",
            "organization": org or self.org,
            "project": project or self.project,
            "lineage": lineage,
        }

        return self._download_with_progress(
            data=data,
            progress_callback=progress_callback,
            desc=desc or f"Downloading {repro_hash[:8]}",
        )
