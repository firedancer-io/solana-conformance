import json
import os
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineageRepro":
        created_at_str = data["CreatedAt"]
        # Handle both RFC3339 formats
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"

        return cls(
            hash=data["Hash"],
            created_at=datetime.fromisoformat(created_at_str),
            count=data["Count"],
            all_verified=data["AllVerified"],
        )


@dataclass
class ReproIndexResponse:
    bundle_id: str
    lineages: Dict[str, List[LineageRepro]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReproIndexResponse":
        lineages = {}
        for lineage_name, repros in data.get("Lineages", {}).items():
            lineages[lineage_name] = [LineageRepro.from_dict(r) for r in repros]

        return cls(
            bundle_id=data.get("BundleID", "00000000-0000-0000-0000-000000000000"),
            lineages=lineages,
        )


@dataclass
class ReproMetadata:
    hash: str
    bundle: str
    lineage: str
    asset: Optional[str]
    artifact_hashes: List[str]
    summary: str
    verified: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReproMetadata":
        return cls(
            hash=data["hash"],
            bundle=data["bundle"],
            lineage=data["lineage"],
            asset=data.get("asset"),
            artifact_hashes=data.get("artifact_hashes", []),
            summary=data.get("summary", ""),
            verified=data.get("verified", False),
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
    ) -> List[ReproMetadata]:
        data = {
            "org": org or self.org,
            "prj": project or self.project,
            "BundleID": bundle_id or "00000000-0000-0000-0000-000000000000",
        }

        response = self._make_request("GET", REPRO_LIST_PATH, data, use_query=True)
        repros = response.get("repros", [])
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
        return ReproMetadata.from_dict(response["repros"])

    def download_artifact_data(
        self,
        artifact_hash: str,
        lineage: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
    ) -> bytes:
        data = {
            "file_name": artifact_hash,
            "kind": "artifact",
            "organization": org or self.org,
            "project": project or self.project,
            "lineage": lineage,
        }

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
            return response.read()

    def download_repro_data(
        self,
        repro_hash: str,
        lineage: str,
        org: Optional[str] = None,
        project: Optional[str] = None,
    ) -> bytes:
        data = {
            "file_name": repro_hash,
            "kind": "repro",
            "organization": org or self.org,
            "project": project or self.project,
            "lineage": lineage,
        }

        url = self.api_origin + STORAGE_DATA_GET_PATH
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/octet-stream",
        }

        query_data = json.dumps(data)
        url = f"{url}?arpc={urllib.parse.quote(query_data)}"

        with self.client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            return response.read()
