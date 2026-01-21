"""
Octane API client for solana-conformance.

This module provides an API client that uses the native Octane orchestrator API
endpoints directly (not the FuzzCorp NG compatibility layer).

Native API endpoints used:
- /api/bugs - List all bugs with full metadata (supports filters: lineages, hashes, statuses, run_id, bundle_id)
- /api/bugs/<hash> - Get single bug by hash
- /api/bugs/<hash>/artifact - Get artifact download URLs
- /api/health - Health check

Key features:
- Server-side filtering: lineages, hashes, statuses, run_id all combined with AND logic
- Direct GCS/S3 downloads: artifacts are downloaded directly from cloud storage
- Reproducible bugs: use statuses=REPRO_BUG_STATUSES or get_reproducible_bugs()

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
HEALTH_PATH = API_PREFIX + "health"
STATS_PATH = API_PREFIX + "stats"
BUNDLES_PATH = API_PREFIX + "bundles"

# Reproducible bug statuses
REPRO_BUG_STATUSES = {
    "reproducible",
    "crash_reproducible",
    "crash_timeout",
    "crash_leak",
    "crash_oom",
    "crash_asan",
}


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

        # Status can come from multiple fields:
        # - "validation_statuses": array from Octane API (e.g., ["reproducible"])
        # - "status": single string (fallback)
        validation_statuses = data.get("validation_statuses")
        if (
            validation_statuses
            and isinstance(validation_statuses, list)
            and len(validation_statuses) > 0
        ):
            # Use the first status from the array (most relevant)
            status = validation_statuses[0]
        else:
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
        """Get all available download URLs in priority order (GCS first, then S3).

        Deprecated: Use get_repro_download_urls(), get_fixture_download_urls(),
        or get_crash_download_urls() instead.
        This method returns repro URLs (.fix with .fuzz fallback) for backwards compatibility.
        """
        return self.get_repro_download_urls()

    def get_repro_download_urls(self) -> List[str]:
        """
        Get download URLs for repro files: .fix first, then .fuzz as fallback.

        Use this for download-repro / download-repros commands.

        Returns:
            List of download URLs in priority order:
            1. Fixture GCS URL (.fix file)
            2. Fixture S3 URL (.fix file)
            3. Artifact GCS URLs (.fuzz files) - fallback
            4. Artifact S3 URLs (.fuzz files) - fallback
        """
        urls = []
        # Fixture URLs first (.fix files)
        if self.fixture_gcs_url:
            urls.append(self.fixture_gcs_url)
        if self.fixture_s3_url:
            urls.append(self.fixture_s3_url)
        # Artifact URLs as fallback (.fuzz files)
        urls.extend(self.artifact_gcs_urls)
        urls.extend(self.artifact_s3_urls)
        return urls

    def get_fixture_download_urls(self) -> List[str]:
        """
        Get download URLs for fixture files (.fix) ONLY - no fallback.

        Use this for download-fixture / download-fixtures commands.

        Returns:
            List of fixture download URLs only (GCS first, then S3).
            Empty list if no fixture URLs available.
        """
        urls = []
        if self.fixture_gcs_url:
            urls.append(self.fixture_gcs_url)
        if self.fixture_s3_url:
            urls.append(self.fixture_s3_url)
        return urls

    def get_crash_download_urls(self) -> List[str]:
        """
        Get download URLs for crash/fuzz files (.fuzz) ONLY - no fallback.

        Use this for download-crash / download-crashes commands.

        Returns:
            List of artifact download URLs only (GCS first, then S3).
            Empty list if no artifact URLs available.
        """
        urls = []
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
    active_lineages: List[str] = field(default_factory=list)

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
            active_lineages=data.get("active_lineages") or [],
        )

    def get_lineages(self) -> Dict[str, List[BugRecord]]:
        """Group bugs by lineage."""
        lineages: Dict[str, List[BugRecord]] = {}
        for bug in self.bugs:
            if bug.lineage not in lineages:
                lineages[bug.lineage] = []
            lineages[bug.lineage].append(bug)
        return lineages

    def get_all_lineages(self) -> Dict[str, List[BugRecord]]:
        """
        Get all lineages including ones with zero bugs.

        Returns a dict where keys are lineage names from active_lineages
        and values are lists of bugs (empty list if no bugs for that lineage).
        """
        lineages: Dict[str, List[BugRecord]] = {}

        # First, add all active lineages with empty lists
        for lineage in self.active_lineages:
            lineages[lineage] = []

        # Then, populate with actual bugs
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
            all_verified=bug.status in REPRO_BUG_STATUSES,
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
        """
        Create a ReproIndexResponse from a BugsResponse.

        Includes all active lineages from the API, even those with zero bugs.
        """
        lineages: Dict[str, List[LineageRepro]] = {}

        # First, add all active lineages with empty lists
        for lineage in response.active_lineages:
            lineages[lineage] = []

        # Then, populate with actual bugs
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
        lineages: Optional[List[str]] = None,
        hashes: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_fixed: bool = False,
    ) -> BugsResponse:
        """
        Get all bugs from the native /api/bugs endpoint.

        All filters are combined with AND logic.

        Args:
            bundle_id: Optional bundle ID to filter by.
            run_id: Optional run ID to filter by.
            lineages: Optional list of lineages to filter by.
            hashes: Optional list of hashes to filter by.
            statuses: Optional list of statuses to filter by (e.g., ["reproducible", "crash_reproducible"]).
            limit: Optional limit on number of bugs returned.
            include_fixed: Whether to include fixed bugs.

        Returns:
            BugsResponse with all bugs.

        Note:
            Using statuses=REPRO_BUG_STATUSES is equivalent to calling get_reproducible_bugs().
        """
        params = {}
        if bundle_id or self.bundle_id:
            params["bundle_id"] = bundle_id or self.bundle_id
        if run_id:
            params["run_id"] = run_id
        if lineages:
            params["lineages"] = ",".join(lineages)
        if hashes:
            params["hashes"] = ",".join(hashes)
        if statuses:
            params["statuses"] = ",".join(statuses)
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
        lineages: Optional[List[str]] = None,
        hashes: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> BugsResponse:
        """
        Get only reproducible bugs.

        This is a convenience method equivalent to calling get_bugs() with:
            statuses=["reproducible", "crash_reproducible", "crash_timeout",
                      "crash_leak", "crash_oom", "crash_asan"]

        All filters are combined with AND logic.

        Args:
            bundle_id: Optional bundle ID to filter by.
            run_id: Optional run ID to filter by.
            lineages: Optional list of lineages to filter by.
            hashes: Optional list of hashes to filter by.
            limit: Optional limit on number of bugs returned.

        Returns:
            BugsResponse with reproducible bugs only.
        """
        return self.get_bugs(
            bundle_id=bundle_id,
            run_id=run_id,
            lineages=lineages,
            hashes=hashes,
            statuses=list(REPRO_BUG_STATUSES),
            limit=limit,
            include_fixed=True,  # Status filter already restricts, don't double-filter
        )

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
        lineages: Optional[List[str]] = None,
        hashes: Optional[List[str]] = None,
    ) -> ReproIndexResponse:
        """
        List all repro lineages with their counts.

        This is a compatibility method that uses the native /api/bugs endpoint
        and groups bugs by lineage.

        Args:
            bundle_id: Optional bundle ID to filter by.
            lineages: Optional list of lineages to filter by (bulk server-side filtering).
            hashes: Optional list of hashes to filter by (bulk server-side filtering).

        Returns:
            ReproIndexResponse with lineages and repro counts.
        """
        bugs_response = self.get_reproducible_bugs(
            bundle_id=bundle_id,
            lineages=lineages,
            hashes=hashes,
        )
        return ReproIndexResponse.from_bugs_response(bugs_response)

    def list_repros_full(
        self,
        bundle_id: Optional[str] = None,
        lineages: Optional[List[str]] = None,
        hashes: Optional[List[str]] = None,
    ) -> List[ReproMetadata]:
        """
        List all repros with full metadata.

        Args:
            bundle_id: Optional bundle ID to filter by.
            lineages: Optional list of lineages to filter by.
            hashes: Optional list of hashes to filter by.

        Returns:
            List of ReproMetadata objects.
        """
        bugs_response = self.get_reproducible_bugs(
            bundle_id=bundle_id,
            lineages=lineages,
            hashes=hashes,
        )
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

                # Try to get project from environment or use a default
                project = os.getenv("GCLOUD_PROJECT") or os.getenv(
                    "GOOGLE_CLOUD_PROJECT"
                )
                if project:
                    self._gcs_client = storage.Client(project=project)
                else:
                    # Let the client try to detect from credentials/environment
                    try:
                        self._gcs_client = storage.Client()
                    except OSError:
                        # If project can't be determined, use anonymous client for public buckets
                        # or a default project for Firedancer fuzzing
                        self._gcs_client = storage.Client(
                            project="isol-firedancer-fuzzing"
                        )
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

    def download_bug_repro(
        self,
        bug: BugRecord,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download repro data for a bug: .fix first, then .fuzz as fallback.

        Use this for download-repro / download-repros commands.

        Args:
            bug: BugRecord with cloud storage URLs.
            progress_callback: Optional callback for progress updates.

        Returns:
            Repro data as bytes (.fix preferred, .fuzz fallback).

        Raises:
            ValueError: If no download URLs are available.
            Exception: If all download attempts fail.
        """
        urls = bug.get_repro_download_urls()

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

        raise last_error or ValueError(f"Failed to download repro for bug {bug.hash}")

    def download_bug_fixture(
        self,
        bug: BugRecord,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download fixture data (.fix file) ONLY for a bug - no fallback to .fuzz.

        Use this for download-fixture / download-fixtures commands.

        Args:
            bug: BugRecord with cloud storage URLs.
            progress_callback: Optional callback for progress updates.

        Returns:
            Fixture data as bytes.

        Raises:
            ValueError: If no fixture URLs are available.
            Exception: If all download attempts fail.
        """
        urls = bug.get_fixture_download_urls()

        if not urls:
            raise ValueError(
                f"No fixture URLs available for bug {bug.hash}. "
                f"Bug may not have a .fix file uploaded."
            )

        last_error = None
        for url in urls:
            try:
                return self._download_from_url(url, progress_callback)
            except Exception as e:
                last_error = e
                continue

        raise last_error or ValueError(f"Failed to download fixture for bug {bug.hash}")

    def download_bug_crash(
        self,
        bug: BugRecord,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download crash data (.fuzz file) ONLY for a bug - no fallback to .fix.

        Use this for download-crash / download-crashes commands.

        Args:
            bug: BugRecord with cloud storage URLs.
            progress_callback: Optional callback for progress updates.

        Returns:
            Crash data as bytes.

        Raises:
            ValueError: If no crash/artifact URLs are available.
            Exception: If all download attempts fail.
        """
        urls = bug.get_crash_download_urls()

        if not urls:
            raise ValueError(
                f"No crash URLs available for bug {bug.hash}. "
                f"Bug may not have a .fuzz file uploaded."
            )

        last_error = None
        for url in urls:
            try:
                return self._download_from_url(url, progress_callback)
            except Exception as e:
                last_error = e
                continue

        raise last_error or ValueError(f"Failed to download crash for bug {bug.hash}")

    def download_bug_artifact(
        self,
        bug: BugRecord,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download artifact data for a bug.

        Deprecated: Use download_bug_repro(), download_bug_fixture(), or download_bug_crash() instead.
        This method uses repro behavior (.fix with .fuzz fallback) for backwards compatibility.

        Args:
            bug: BugRecord with cloud storage URLs.
            progress_callback: Optional callback for progress updates.

        Returns:
            Artifact data as bytes.

        Raises:
            ValueError: If no download URLs are available.
            Exception: If all download attempts fail.
        """
        return self.download_bug_repro(bug, progress_callback)

    def download_repro_data(
        self,
        repro_hash: str,
        lineage: str,
        bundle_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        """
        Download repro data by hash: .fix first, then .fuzz as fallback.

        Use this for download-repro / download-repros commands.
        Downloads directly from cloud storage (GCS/S3), never proxied through Octane.

        Args:
            repro_hash: Hash of the repro to download.
            lineage: Lineage name for the repro.
            bundle_id: Optional bundle ID.
            progress_callback: Optional callback for progress updates.
            desc: Optional description for progress display.

        Returns:
            Repro data as bytes (.fix preferred, .fuzz fallback).
        """
        # Get bug metadata - let ValueError propagate if bug not found
        bug = self.get_bug_by_hash(repro_hash, bundle_id=bundle_id, lineage=lineage)
        # Download repro - let ValueError propagate if no URLs available
        return self.download_bug_repro(bug, progress_callback)

    def download_fixture_data(
        self,
        artifact_hash: str,
        lineage: str,
        bundle_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        """
        Download fixture data (.fix file) ONLY by hash - no fallback to .fuzz.

        Use this for download-fixture / download-fixtures commands.
        Downloads directly from cloud storage (GCS/S3), never proxied through Octane.

        Args:
            artifact_hash: Hash of the artifact (bug hash) to download.
            lineage: Lineage name for the artifact.
            bundle_id: Optional bundle ID.
            progress_callback: Optional callback for progress updates.
            desc: Optional description for progress display.

        Returns:
            Fixture data as bytes.

        Raises:
            ValueError: If no fixture URL available for this bug.
        """
        # Get bug metadata - let ValueError propagate if bug not found
        bug = self.get_bug_by_hash(artifact_hash, bundle_id=bundle_id, lineage=lineage)
        # Download fixture - let ValueError propagate if no fixture URLs
        return self.download_bug_fixture(bug, progress_callback)

    def download_crash_data(
        self,
        crash_hash: str,
        lineage: str,
        bundle_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        desc: Optional[str] = None,
    ) -> bytes:
        """
        Download crash data (.fuzz file) ONLY by hash - no fallback to .fix.

        Use this for download-crash / download-crashes commands.
        Downloads directly from cloud storage (GCS/S3), never proxied through Octane.

        Args:
            crash_hash: Hash of the crash (bug hash) to download.
            lineage: Lineage name for the crash.
            bundle_id: Optional bundle ID.
            progress_callback: Optional callback for progress updates.
            desc: Optional description for progress display.

        Returns:
            Crash data as bytes.

        Raises:
            ValueError: If no crash/artifact URL available for this bug.
        """
        # Get bug metadata - let ValueError propagate if bug not found
        bug = self.get_bug_by_hash(crash_hash, bundle_id=bundle_id, lineage=lineage)
        # Download crash - let ValueError propagate if no crash URLs
        return self.download_bug_crash(bug, progress_callback)

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

        Deprecated: Use download_repro_data(), download_fixture_data(), or download_crash_data() instead.
        This method uses repro behavior (.fix with .fuzz fallback) for backwards compatibility.

        Args:
            artifact_hash: Hash of the artifact (bug hash) to download.
            lineage: Lineage name for the artifact.
            bundle_id: Optional bundle ID.
            progress_callback: Optional callback for progress updates.
            desc: Optional description for progress display.

        Returns:
            Artifact data as bytes.
        """
        return self.download_repro_data(
            repro_hash=artifact_hash,
            lineage=lineage,
            bundle_id=bundle_id,
            progress_callback=progress_callback,
            desc=desc,
        )
