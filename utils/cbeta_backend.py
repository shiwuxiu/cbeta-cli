"""CBETA API backend - HTTP client for api.cbetaonline.cn."""

import requests
import urllib3
import time
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

# Disable SSL warnings for Windows compatibility
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_BASE_URL = "https://api.cbetaonline.cn"
TIMEOUT = 30


class CbetaClient:
    """HTTP client for CBETA API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, referer: str = "cli-anything-cbeta", use_cache: bool = True):
        self.base_url = base_url.rstrip("/")
        self.referer = referer
        self.use_cache = use_cache
        self.session = requests.Session()
        self.session.headers.update({
            "Referer": referer,
            "Accept": "application/json",
            "User-Agent": "cli-anything-cbeta/1.0.0"
        })

        # 缓存管理器
        if use_cache:
            from cli_anything.cbeta.utils.cache import get_cache
            self._cache = get_cache()
        else:
            self._cache = None

    def _request(self, endpoint: str, params: Optional[Dict] = None, cache: bool = True) -> Dict | List:
        """Make HTTP request to CBETA API.

        Args:
            endpoint: API endpoint
            params: Request parameters
            cache: Whether to use cache (default True)
        """
        # 检查缓存
        if self.use_cache and cache and self._cache:
            cached_result = self._cache.get(endpoint, params)
            if cached_result is not None:
                return cached_result

        url = f"{self.base_url}/{endpoint}"
        start_time = time.time()
        try:
            resp = self.session.get(url, params=params, timeout=TIMEOUT, verify=False)
            resp.raise_for_status()
            result = resp.json()
            duration_ms = (time.time() - start_time) * 1000

            # 记录 API 请求日志
            from cli_anything.cbeta.utils.logger import get_logger
            get_logger().log_api_request(endpoint, params or {}, duration_ms, True)

            # 写入缓存
            if self.use_cache and cache and self._cache:
                self._cache.set(endpoint, params, result)

            return result
        except requests.exceptions.JSONDecodeError:
            # health endpoint returns plain text
            return {"status": resp.text.strip()}
        except requests.exceptions.RequestException as e:
            duration_ms = (time.time() - start_time) * 1000
            from cli_anything.cbeta.utils.logger import get_logger
            get_logger().log_api_request(endpoint, params or {}, duration_ms, False)
            raise RuntimeError(f"API request failed: {e}")

    # ── Health / Server ────────────────────────────────────────────
    def health(self) -> Dict:
        """Check API health status."""
        return self._request("health")

    def report_total(self) -> Dict:
        """Get statistics report."""
        return self._request("report/total")

    # ── Search ──────────────────────────────────────────────────────
    def search(self, q: str, **kwargs) -> Dict:
        """Basic search.

        Args:
            q: Query string (required)
            start: Start index (default 0)
            rows: Number of results (default 10)
            around: Context lines around matches
            canon: Canon filter (T, X, K, etc.)
            category: Category filter
            work: Work ID filter
            creator: Creator filter
            dynasty: Dynasty filter
        """
        params = {"q": q}
        params.update(kwargs)
        return self._request("search", params)

    def search_all_in_one(self, q: str, **kwargs) -> Dict:
        """All-in-one search (supports NEAR, Exclude syntax)."""
        params = {"q": q}
        params.update(kwargs)
        return self._request("search/all_in_one", params)

    def search_kwic(self, q: str, **kwargs) -> Dict:
        """KWIC (Key Word In Context) search."""
        params = {"q": q}
        params.update(kwargs)
        return self._request("search/kwic", params)

    def search_facet(self, facet_by: str, q: Optional[str] = None, **kwargs) -> Dict:
        """Facet search for statistics."""
        params = {"facet_by": facet_by}
        if q:
            params["q"] = q
        params.update(kwargs)
        return self._request("search/facet", params)

    def search_similar(self, work: str, juan: Optional[int] = None, **kwargs) -> Dict:
        """Similar text search."""
        params = {"work": work}
        if juan:
            params["juan"] = juan
        params.update(kwargs)
        return self._request("search/similar", params)

    def search_notes(self, q: str, **kwargs) -> Dict:
        """Search in annotations/notes."""
        params = {"q": q}
        params.update(kwargs)
        return self._request("search/notes", params)

    def search_title(self, q: str, **kwargs) -> Dict:
        """Search by title."""
        params = {"q": q}
        params.update(kwargs)
        return self._request("search/title", params)

    def search_variants(self, q: str, **kwargs) -> Dict:
        """Search with variant characters."""
        params = {"q": q}
        params.update(kwargs)
        return self._request("search/variants", params)

    # ── Works ───────────────────────────────────────────────────────
    def works(self, **kwargs) -> Dict:
        """Search works (canonical texts).

        Args:
            work: Work ID (e.g., T0001, A001)
            creator: Creator text search
            creator_id: Creator ID search
            vol_start/vol_end: Volume range (with canon)
            work_start/work_end: Work number range (with canon)
            time_start/time_end: Time range (years)
            dynasty: Dynasty filter
            uuid: Canon UUID
        """
        return self._request("works", kwargs)

    def work_toc(self, work: str) -> Dict:
        """Get table of contents for a work."""
        return self._request("works/toc", {"work": work})

    def work_word_count(self, **kwargs) -> Dict:
        """Export word count statistics."""
        return self._request("works/word_count", kwargs)

    # ── Lines ───────────────────────────────────────────────────────
    def lines(self, linehead: str, before: int = 0, after: int = 0) -> Dict:
        """Get lines by linehead.

        Args:
            linehead: Line header identifier
            before: Number of lines before
            after: Number of lines after
        """
        params = {"linehead": linehead}
        if before > 0:
            params["before"] = before
        if after > 0:
            params["after"] = after
        return self._request("lines", params)

    def lines_range(self, linehead_start: str, linehead_end: str) -> Dict:
        """Get lines within a range."""
        params = {
            "linehead_start": linehead_start,
            "linehead_end": linehead_end
        }
        return self._request("lines", params)

    # ── Juans (Volumes) ─────────────────────────────────────────────
    def juans(self, work: str) -> Dict:
        """Get juans (volumes) for a work."""
        return self._request("juans", {"work": work})

    def juan_goto(self, work: str, juan: int) -> Dict:
        """Go to specific juan."""
        return self._request("juans/goto", {"work": work, "juan": juan})

    # ── Catalog ─────────────────────────────────────────────────────
    def catalog_entry(self, entry: str) -> Dict:
        """Get catalog entry details."""
        return self._request("catalog_entry", {"entry": entry})

    def category(self, category: str) -> Dict:
        """Get works by category."""
        return self._request(f"category/{category}")

    # ── TOC ──────────────────────────────────────────────────────────
    def toc(self, work: str) -> Dict:
        """Get table of contents."""
        return self._request("toc", {"work": work})

    # ── Download ─────────────────────────────────────────────────────
    def download_info(self, work_id: str) -> Dict:
        """Get download info for a work."""
        return self._request(f"download/{work_id}")

    # ── Export ───────────────────────────────────────────────────────
    def export_all_works(self) -> Dict:
        """Export all works list."""
        return self._request("export/all_works")

    def export_all_creators(self) -> Dict:
        """Export all creators list."""
        return self._request("export/all_creators")

    def export_dynasty(self) -> Dict:
        """Export dynasty information."""
        return self._request("export/dynasty")

    # ── Chinese Tools ────────────────────────────────────────────────
    def sc2tc(self, text: str) -> Dict:
        """Simplified Chinese to Traditional Chinese conversion."""
        return self._request("chinese_tools/sc2tc", {"text": text})

    # ── Word Segmentation ────────────────────────────────────────────
    def word_seg(self, text: str) -> Dict:
        """Word segmentation."""
        return self._request("word_seg", {"text": text})

    # ── Changes ──────────────────────────────────────────────────────
    def changes(self, **kwargs) -> Dict:
        """Get change history."""
        return self._request("changes", kwargs)

    # ── Content by Work/Juan/Edition ─────────────────────────────────
    def work_content(self, work_id: str, juan: int, edition: Optional[str] = None) -> Dict:
        """Get content of a specific work/juan/edition."""
        endpoint = f"work/{work_id}/juan/{juan}"
        if edition:
            endpoint += f"/edition/{edition}"
        return self._request(endpoint)