"""
Octane API client for solana-conformance.

This module provides an API client that uses the native Octane orchestrator API
endpoints directly (not the FuzzCorp NG compatibility layer).

Native API endpoints used:
- /api/bugs - List all bugs with full metadata
- /api/bugs/reproducible - Only reproducible bugs (crash_reproducible, etc.)
- /api/health - Health check

The client supports downloading artifacts directly from GCS/S3 URLs
stored in the bug metadata.

Default API endpoint: gusc1b-fdfuzz-orchestrator1.jumpisolated.com:5000
"""

import io
import json
import os
import urllib.parse
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
import httpx

# Default Octane API endpoint
DEFAULT_OCTANE_API_ORIGIN = "http://gusc1b-fdfuzz-orchestrator1.jumpisolated.com:5000"

# Native Octane API endpoints
API_PREFIX = "/api/"
BUGS_PATH = API_PREFIX + "bugs"
BUGS_REPRODUCIBLE_PATH = API_PREFIX + "bugs/reproducible"
HEALTH_PATH = API_PREFIX + "health"
STATS_PATH = API_PREFIX + "stats"
BUNDLES_PATH = API_PREFIX + "bundles"


@dataclass
class BugRecord:
    """
    Represents a bug record from the native Octane API.

    Contains all metadata including cloud storage URLs for direct downloads.
    """

    hash: str  # Bug fingerprint hash
    bundle_id: str
    lineage: str
    status: str

    # Optional fields from DB
    asset: Optional[str] = None
    summary: Optional[str] = None
    flaky: bool = False

    # Artifact information
    artifact_hashes: List[str] = field(default_factory=list)
    bug_paths: List[str] = field(default_factory=list)

    # Cloud storage URLs (from source metadata)
    fixture_gcs_url: Optional[str] = None
    fixture_s3_url: Optional[str] = None
    artifact_gcs_urls: List[str] = field(default_factory=list)
    artifact_s3_urls: List[str] = field(default_factory=list)

    # Additional metadata
    run_id: Optional[str] = None
    created_at: Optional[datetime] = None
    reproduced_at: Optional[datetime] = None
    fixed_at: Optional[datetime] = None

    # Raw source metadata for fallback
    source: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugRecord":
        """Create a BugRecord from API response dict."""
        # Core identifiers
        hash_val = data.get("hash") or data.get("bug_hash") or data.get("fingerprint")
        if not hash_val:
            raise KeyError("hash/bug_hash/fingerprint is required")

        bundle_id = data.get("bundle_id") or data.get("bundle") or ""
        lineage = data.get("lineage") or data.get("target_name") or ""
        status = data.get("status") or "unknown"

        # Optional fields
        asset = data.get("asset")
        summary = data.get("summary") or data.get("description") or ""
        flaky = bool(data.get("flaky", False))

        # Artifact hashes
        artifact_hashes = data.get("artifact_hashes") or []
        if isinstance(artifact_hashes, str):
            artifact_hashes = [artifact_hashes]

        # Bug paths (local filesystem paths)
        bug_paths = data.get("bug_paths") or []
        if isinstance(bug_paths, str):
            bug_paths = [bug_paths]

        # Extract source metadata for cloud URLs
        source = data.get("source") or {}
        fixture_gcs_url = source.get("fixture_gcs_url") or data.get("fixture_gcs_url")
        fixture_s3_url = source.get("fixture_s3_url") or data.get("fixture_s3_url")

        # Artifact URLs can be in source or at top level
        artifact_gcs_urls = (
            source.get("artifact_gcs_urls") or data.get("artifact_gcs_urls") or []
        )
        artifact_s3_urls = (
            source.get("artifact_s3_urls") or data.get("artifact_s3_urls") or []
        )
        if isinstance(artifact_gcs_urls, str):
            artifact_gcs_urls = [artifact_gcs_urls]
        if isinstance(artifact_s3_urls, str):
            artifact_s3_urls = [artifact_s3_urls]

        # Timestamps
        created_at = None
        if data.get("created_at"):
            try:
                created_at_str = data["created_at"]
                if isinstance(created_at_str, str):
                    if created_at_str.endswith("Z"):
                        created_at_str = created_at_str[:-1] + "+00:00"
                    created_at = datetime.fromisoformat(created_at_str)
            except (ValueError, TypeError):
                pass

        reproduced_at = None
        if data.get("reproduced_at"):
            try:
                reproduced_at_str = data["reproduced_at"]
                if isinstance(reproduced_at_str, str):
                    if reproduced_at_str.endswith("Z"):
                        reproduced_at_str = reproduced_at_str[:-1] + "+00:00"
                    reproduced_at = datetime.fromisoformat(reproduced_at_str)
            except (ValueError, TypeError):
                pass

        return cls(
            hash=hash_val,
            bundle_id=str(bundle_id),
            lineage=lineage,
            status=status,
            asset=asset,
            summary=summary,
            flaky=flaky,
            artifact_hashes=list(artifact_hashes),
            bug_paths=list(bug_paths),
            fixture_gcs_url=fixture_gcs_url,
            fixture_s3_url=fixture_s3_url,
            artifact_gcs_urls=list(artifact_gcs_urls),
            artifact_s3_urls=list(artifact_s3_urls),
            run_id=data.get("run_id"),
            created_at=created_at,
            reproduced_at=reproduced_at,
            source=source if source else None,
        )

    def get_download_urls(self) -> List[str]:
        """Get all available download URLs in priority order (GCS first, then S3)."""
        urls = []

        # Fixture URLs first (preferred)
        if self.fixture_gcs_url:
            urls.append(self.fixture_gcs_url)
        if self.fixture_s3_url:
            urls.append(self.fixture_s3_url)

        # Then artifact URLs
        urls.extend(self.artifact_gcs_urls)
        urls.extend(self.artifact_s3_urls)

        return urls


@dataclass
class BugsResponse:
    """Response from /api/bugs endpoint."""

    total_bugs: int
    bugs: List[BugRecord]
    bundle_id: str
    source: str
    filtered: bool = False

    # Additional metadata
    run_id_filter: Optional[str] = None
    total_bugs_scope: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugsResponse":
        """Create a BugsResponse from API response dict."""
        bugs_data = data.get("bugs") or []
        bugs = [BugRecord.from_dict(bug) for bug in bugs_data]

        return cls(
            total_bugs=data.get("total_bugs", len(bugs)),
            bugs=bugs,
            bundle_id=data.get("bundle_id", ""),
            source=data.get("source", "unknown"),
            filtered=data.get("filtered", False),
            run_id_filter=data.get("run_id_filter"),
            total_bugs_scope=data.get("total_bugs_scope"),
        )

    def get_lineages(self) -> Dict[str, List[BugRecord]]:
        """Group bugs by lineage."""
        lineages: Dict[str, List[BugRecord]] = {}
        for bug in self.bugs:
            if bug.lineage not in lineages:
                lineages[bug.lineage] = []
            lineages[bug.lineage].append(bug)
        return lineages


@dataclass
class LineageRepro:
    """
    Represents a repro/bug within a lineage.

    This is a compatibility wrapper that provides the same interface
    as the FuzzCorpAPIClient for use with existing test_suite code.
    """

    hash: str
    created_at: datetime
    count: int
    all_verified: bool
    drivers: Optional[List[str]] = None
    config_indices: Optional[List[int]] = None

    # Extended fields from native API
    status: Optional[str] = None
    bug_record: Optional[BugRecord] = None

    @classmethod
    def from_bug_record(cls, bug: BugRecord) -> "LineageRepro":
        """Create a LineageRepro from a BugRecord."""
        return cls(
            hash=bug.hash,
            created_at=bug.created_at or datetime.min,
            count=1,  # Each bug is one repro
            all_verified=bug.status
            in ("reproducible", "crash_reproducible", "verified"),
            status=bug.status,
            bug_record=bug,
        )


@dataclass
class ReproIndexResponse:
    """
    Compatibility wrapper for list_repros response.

    Groups bugs by lineage to match FuzzCorpAPIClient interface.
    """

    bundle_id: str
    lineages: Dict[str, List[LineageRepro]]

    @classmethod
    def from_bugs_response(cls, response: BugsResponse) -> "ReproIndexResponse":
        """Create a ReproIndexResponse from a BugsResponse."""
        lineages: Dict[str, List[LineageRepro]] = {}

        for bug in response.bugs:
            if bug.lineage not in lineages:
                lineages[bug.lineage] = []
            lineages[bug.lineage].append(LineageRepro.from_bug_record(bug))

        return cls(
            bundle_id=response.bundle_id,
            lineages=lineages,
        )


@dataclass
class ReproMetadata:
    """
    Compatibility wrapper for repro metadata.

    Provides the same interface as FuzzCorpAPIClient.ReproMetadata.
    """

    hash: str
    bundle: str
    lineage: str
    asset: Optional[str]
    artifact_hashes: List[str]
    summary: str
    flaky: bool

    # Extended fields from native API
    status: Optional[str] = None
    bug_record: Optional[BugRecord] = None

    @classmethod
    def from_bug_record(cls, bug: BugRecord) -> "ReproMetadata":
        """Create a ReproMetadata from a BugRecord."""
        return cls(
            hash=bug.hash,
            bundle=bug.bundle_id,
            lineage=bug.lineage,
            asset=bug.asset,
            artifact_hashes=bug.artifact_hashes,
            summary=bug.summary or "",
            flaky=bug.flaky,
            status=bug.status,
            bug_record=bug,
        )


class OctaneAPIClient:
    """
    API client for the native Octane orchestrator API.

    This client uses the native Octane API endpoints (/api/bugs, etc.)
    instead of the FuzzCorp NG compatibility layer.

    IMPORTANT: All artifact downloads are performed directly from cloud storage
    (GCS/S3). The Octane API only provides metadata and download URLs, it never
    proxies artifact bytes.

    Requires google-cloud-storage and/or boto3 for direct cloud downloads.
    Install with: pip install "solana-conformance[octane]"
    """

    def __init__(
        self,
        api_origin: Optional[str] = None,
        bundle_id: Optional[str] = None,
        verify_ssl: bool = True,
        http2: bool = True,
        timeout: float = 300.0,
    ):
        """
        Initialize the Octane API client.

        Args:
            api_origin: Octane API origin URL. Defaults to environment variable
                       OCTANE_API_URL or DEFAULT_OCTANE_API_ORIGIN.
            bundle_id: Optional bundle ID to use for queries.
            verify_ssl: Whether to verify SSL certificates.
            http2: Whether to use HTTP/2.
            timeout: Request timeout in seconds.
        """
        self.api_origin = (
            api_origin
            or os.getenv("OCTANE_API_URL")
            or os.getenv("OCTANE_API_ORIGIN")
            or DEFAULT_OCTANE_API_ORIGIN
        ).rstrip("/")

        self.bundle_id = bundle_id or os.getenv("OCTANE_BUNDLE_ID")

        self.client = httpx.Client(
            verify=verify_ssl,
            http2=http2,
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

        # GCS/S3 clients for direct downloads (lazily initialized)
        self._gcs_client = None
        self._s3_client = None

    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request to the Octane server."""
        url = self.api_origin + path

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if method.upper() == "GET":
            response = self.client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = self.client.post(url, json=json_data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Check if the Octane API is healthy."""
        try:
            response = self._make_request("GET", HEALTH_PATH)
            return response.get("status") == "healthy"
        except Exception:
            return False

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # ========================================================================
    # Native Octane API methods
    # ========================================================================

    def get_bugs(
        self,
        bundle_id: Optional[str] = None,
        run_id: Optional[str] = None,
        lineage: Optional[str] = None,
        limit: Optional[int] = None,
        include_fixed: bool = False,
    ) -> BugsResponse:
        """
        Get all bugs from the native /api/bugs endpoint.

        Args:
            bundle_id: Optional bundle ID to filter by.
            run_id: Optional run ID to filter by.
            lineage: Optional lineage (target name) to filter by.
            limit: Optional limit on number of bugs returned.
            include_fixed: Whether to include fixed bugs.

        Returns:
            BugsResponse with all bugs.
        """
        params = {}
        if bundle_id or self.bundle_id:
            params["bundle_id"] = bundle_id or self.bundle_id
        if run_id:
            params["run_id"] = run_id
        if lineage:
            params["lineage"] = lineage
        if limit:
            params["limit"] = str(limit)
        if include_fixed:
            params["include_fixed"] = "true"

        response = self._make_request("GET", BUGS_PATH, params=params)
        return BugsResponse.from_dict(response)

    def get_reproducible_bugs(
        self,
        bundle_id: Optional[str] = None,
        run_id: Optional[str] = None,
        lineage: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> BugsResponse:
        """
        Get only reproducible bugs from the native /api/bugs/reproducible endpoint.

        This returns bugs with status: reproducible, crash_reproducible,
        crash_timeout, crash_leak, crash_oom, crash_asan.

        Args:
            bundle_id: Optional bundle ID to filter by.
            run_id: Optional run ID to filter by.
            lineage: Optional lineage (target name) to filter by.
            limit: Optional limit on number of bugs returned.

        Returns:
            BugsResponse with reproducible bugs only.
        """
        params = {}
        if bundle_id or self.bundle_id:
            params["bundle_id"] = bundle_id or self.bundle_id
        if run_id:
            params["run_id"] = run_id
        if lineage:
            params["lineage"] = lineage
        if limit:
            params["limit"] = str(limit)

        response = self._make_request("GET", BUGS_REPRODUCIBLE_PATH, params=params)
        return BugsResponse.from_dict(response)

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics from /api/stats."""
        return self._make_request("GET", STATS_PATH)

    def get_bundle_manifest(self, bundle_id: str) -> Dict[str, Any]:
        """Get bundle manifest by bundle ID."""
        return self._make_request("GET", f"{BUNDLES_PATH}/{bundle_id}")

    def get_bug_by_hash(
        self,
        bug_hash: str,
        bundle_id: Optional[str] = None,
        lineage: Optional[str] = None,
    ) -> BugRecord:
        """
        Get a single bug by its hash using the native /api/bugs/<hash> endpoint.

        Args:
            bug_hash: The bug fingerprint hash.
            bundle_id: Optional bundle ID filter.
            lineage: Optional lineage filter.

        Returns:
            BugRecord for the bug.

        Raises:
            ValueError: If bug not found.
        """
        params = {}
        if bundle_id or self.bundle_id:
            params["bundle_id"] = bundle_id or self.bundle_id
        if lineage:
            params["lineage"] = lineage

        try:
            response = self._make_request(
                "GET", f"{BUGS_PATH}/{bug_hash}", params=params
            )
            bug_data = response.get("bug")
            if not bug_data:
                raise ValueError(f"No bug found for hash: {bug_hash}")
            return BugRecord.from_dict(bug_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"No bug found for hash: {bug_hash}")
            raise

    def get_bugs_bulk(
        self,
        hashes: Optional[List[str]] = None,
        lineages: Optional[List[str]] = None,
        bundle_id: Optional[str] = None,
        include_artifacts: bool = False,
    ) -> BugsResponse:
        """
        Bulk fetch bug metadata for multiple hashes and/or lineages.

        This is more efficient than fetching all bugs or making N separate requests.

        Args:
            hashes: List of bug hashes to fetch.
            lineages: List of lineages to filter by.
            bundle_id: Optional bundle ID filter.
            include_artifacts: If true, include artifact download URLs.

        Returns:
            BugsResponse with the requested bugs.

        Raises:
            ValueError: If neither hashes nor lineages are provided.
        """
        if not hashes and not lineages:
            raise ValueError("At least one of 'hashes' or 'lineages' must be provided")

        payload: Dict[str, Any] = {}
        if hashes:
            payload["hashes"] = hashes
        if lineages:
            payload["lineages"] = lineages
        if bundle_id or self.bundle_id:
            payload["bundle_id"] = bundle_id or self.bundle_id
        if include_artifacts:
            payload["include_artifacts"] = True

        response = self._make_request("POST", f"{BUGS_PATH}/bulk", json_data=payload)
        return BugsResponse.from_dict(response)

    def get_artifact_download_urls(
        self,
        bug_hash: str,
        bundle_id: Optional[str] = None,
        lineage: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Get download URLs for a bug's artifact from the native API.

        Args:
            bug_hash: The bug fingerprint hash.
            bundle_id: Optional bundle ID filter.
            lineage: Optional lineage filter.

        Returns:
            List of download URL dicts with 'type' (gcs/s3) and 'url' keys.
        """
        params = {}
        if bundle_id or self.bundle_id:
            params["bundle_id"] = bundle_id or self.bundle_id
        if lineage:
            params["lineage"] = lineage

        response = self._make_request(
            "GET", f"{BUGS_PATH}/{bug_hash}/artifact", params=params
        )
        return response.get("download_urls", [])

    def download_bug_artifact_native(
        self,
        bug_hash: str,
        bundle_id: Optional[str] = None,
        lineage: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download bug artifact by first getting URLs from API, then downloading directly from GCS/S3.

        This is the preferred method as it downloads directly from cloud storage
        without proxying through the Octane server.

        Args:
            bug_hash: The bug fingerprint hash.
            bundle_id: Optional bundle ID filter.
            lineage: Optional lineage filter.
            progress_callback: Optional callback for progress updates.

        Returns:
            Artifact data as bytes (usually a ZIP file).
        """
        # Get download URLs from the API
        download_urls = self.get_artifact_download_urls(bug_hash, bundle_id, lineage)

        if not download_urls:
            raise ValueError(f"No download URLs available for bug {bug_hash}")

        # Try each URL in order (GCS first, then S3)
        last_error = None
        for url_info in download_urls:
            url = url_info.get("url")
            if not url:
                continue
            try:
                return self._download_from_url(url, progress_callback)
            except Exception as e:
                last_error = e
                continue

        raise last_error or ValueError(
            f"Failed to download artifact for bug {bug_hash}"
        )

    # ========================================================================
    # Compatibility methods (same interface as FuzzCorpAPIClient)
    # ========================================================================

    def list_repros(
        self,
        bundle_id: Optional[str] = None,
    ) -> ReproIndexResponse:
        """
        List all repro lineages with their counts.

        This is a compatibility method that uses the native /api/bugs endpoint
        and groups bugs by lineage.

        Args:
            bundle_id: Optional bundle ID to filter by.

        Returns:
            ReproIndexResponse with lineages and repro counts.
        """
        bugs_response = self.get_reproducible_bugs(bundle_id=bundle_id)
        return ReproIndexResponse.from_bugs_response(bugs_response)

    def list_repros_full(
        self,
        bundle_id: Optional[str] = None,
        lineage: Optional[str] = None,
    ) -> List[ReproMetadata]:
        """
        List all repros with full metadata.

        Args:
            bundle_id: Optional bundle ID to filter by.
            lineage: Optional lineage to filter by (server-side filtering).

        Returns:
            List of ReproMetadata objects.
        """
        # Use server-side lineage filtering for efficiency
        bugs_response = self.get_reproducible_bugs(bundle_id=bundle_id, lineage=lineage)
        return [ReproMetadata.from_bug_record(bug) for bug in bugs_response.bugs]

    def get_repro_by_hash(
        self,
        repro_hash: str,
        bundle_id: Optional[str] = None,
        lineage: Optional[str] = None,
    ) -> ReproMetadata:
        """
        Get metadata for a specific repro by hash.

        Uses the native /api/bugs/<hash> endpoint for efficient single-bug lookup.

        Args:
            repro_hash: Hash of the repro to retrieve.
            bundle_id: Optional bundle ID.
            lineage: Optional lineage filter.

        Returns:
            ReproMetadata for the repro.
        """
        # Use native endpoint for efficient single-bug lookup
        bug = self.get_bug_by_hash(repro_hash, bundle_id=bundle_id, lineage=lineage)
        return ReproMetadata.from_bug_record(bug)

    # ========================================================================
    # Direct GCS/S3 download methods
    # ========================================================================

    def _get_gcs_client(self):
        """Get or create a GCS client."""
        if self._gcs_client is None:
            try:
                from google.cloud import storage

                self._gcs_client = storage.Client()
            except ImportError:
                raise ImportError(
                    "google-cloud-storage is required for GCS downloads. "
                    "Install with: pip install google-cloud-storage"
                )
        return self._gcs_client

    def _get_s3_client(self):
        """Get or create an S3 client."""
        if self._s3_client is None:
            try:
                import boto3

                self._s3_client = boto3.client("s3")
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3 downloads. "
                    "Install with: pip install boto3"
                )
        return self._s3_client

    def _download_from_gcs(
        self,
        url: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """Download artifact bytes from a GCS URL (gs://bucket/object)."""
        parsed = urllib.parse.urlparse(url)
        bucket_name = parsed.netloc
        object_name = parsed.path.lstrip("/")

        if not bucket_name or not object_name:
            raise ValueError(f"Malformed GCS URL: {url}")

        client = self._get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)

        data = buffer.getvalue()

        # Update shared progress bar
        try:
            import test_suite.globals as globals

            if globals.download_progress_bar is not None:
                globals.download_progress_bar.update(len(data))
        except:
            pass

        return data

    def _download_from_s3(
        self,
        url: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """Download artifact bytes from an S3 URL (s3://bucket/key)."""
        parsed = urllib.parse.urlparse(url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        if not bucket or not key:
            raise ValueError(f"Malformed S3 URL: {url}")

        client = self._get_s3_client()
        buffer = io.BytesIO()
        client.download_fileobj(bucket, key, buffer)
        buffer.seek(0)

        data = buffer.getvalue()

        # Update shared progress bar
        try:
            import test_suite.globals as globals

            if globals.download_progress_bar is not None:
                globals.download_progress_bar.update(len(data))
        except:
            pass

        return data

    def _download_from_url(
        self,
        url: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """Download from a URL (GCS, S3, or HTTP)."""
        if url.startswith("gs://"):
            return self._download_from_gcs(url, progress_callback)
        elif url.startswith("s3://"):
            return self._download_from_s3(url, progress_callback)
        elif url.startswith("http://") or url.startswith("https://"):
            # HTTP download
            response = self.client.get(url)
            response.raise_for_status()
            data = response.content

            # Update shared progress bar
            try:
                import test_suite.globals as globals

                if globals.download_progress_bar is not None:
                    globals.download_progress_bar.update(len(data))
            except:
                pass

            return data
        else:
            raise ValueError(f"Unsupported URL scheme: {url}")

    def download_bug_artifact(
        self,
        bug: BugRecord,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download artifact data for a bug.

        Tries cloud storage URLs in priority order (GCS first, then S3).

        Args:
            bug: BugRecord with cloud storage URLs.
            progress_callback: Optional callback for progress updates.

        Returns:
            Artifact data as bytes (usually a ZIP file).

        Raises:
            ValueError: If no download URLs are available.
            Exception: If all download attempts fail.
        """
        urls = bug.get_download_urls()

        if not urls:
            raise ValueError(
                f"No download URLs available for bug {bug.hash}. "
                f"Bug may not have cloud-stored artifacts."
            )

        last_error = None
        for url in urls:
            try:
                return self._download_from_url(url, progress_callback)
            except Exception as e:
                last_error = e
                continue

        raise last_error or ValueError(f"Failed to download bug {bug.hash}")

    def download_artifact_data(
        self,
        artifact_hash: str,
        lineage: str,
        bundle_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        """
        Download artifact data by hash.

        Downloads directly from cloud storage (GCS/S3), never proxied through Octane.
        Uses the /api/bugs/<hash>/artifact endpoint to get download URLs, then
        downloads directly from the cloud.

        Args:
            artifact_hash: Hash of the artifact (bug hash) to download.
            lineage: Lineage name for the artifact.
            bundle_id: Optional bundle ID.
            progress_callback: Optional callback for progress updates.
            desc: Optional description for progress display.

        Returns:
            Artifact data as bytes.
        """
        # Primary: Get URLs from API, download directly from cloud
        try:
            return self.download_bug_artifact_native(
                bug_hash=artifact_hash,
                bundle_id=bundle_id,
                lineage=lineage,
                progress_callback=progress_callback,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise
            # Fall through to try getting URLs from bug metadata
        except Exception:
            # Fall through to try getting URLs from bug metadata
            pass

        # Fallback: Get bug metadata and download directly from cloud URLs
        try:
            bug = self.get_bug_by_hash(
                artifact_hash, bundle_id=bundle_id, lineage=lineage
            )
            return self.download_bug_artifact(bug, progress_callback)
        except ValueError:
            pass

        raise ValueError(f"No bug found for hash: {artifact_hash}")

    def download_repro_data(
        self,
        repro_hash: str,
        lineage: str,
        bundle_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        """
        Download repro data by hash.

        This is a compatibility method that calls download_artifact_data.

        Args:
            repro_hash: Hash of the repro to download.
            lineage: Lineage name for the repro.
            bundle_id: Optional bundle ID.
            progress_callback: Optional callback for progress updates.
            desc: Optional description for progress display.

        Returns:
            Repro data as bytes.
        """
        return self.download_artifact_data(
            artifact_hash=repro_hash,
            lineage=lineage,
            bundle_id=bundle_id,
            progress_callback=progress_callback,
            desc=desc,
        )
