from __future__ import annotations

import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEO_ACCESSION_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"


class GeoMetadataFetchError(RuntimeError):
    def __init__(self, error_code: str, message: str = "") -> None:
        super().__init__(message or error_code)
        self.error_code = error_code


def fetch_geo_accession_metadata(gse_id: str, timeout: float = 15.0) -> str:
    accession = (gse_id or "").strip().upper()
    if not accession.startswith("GSE"):
        raise GeoMetadataFetchError("accession_not_found", "GSE accession is required.")

    url = f"{GEO_ACCESSION_URL}?{urlencode({'acc': accession})}"
    request = Request(
        url,
        headers={"User-Agent": "model9-geo-readiness/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except socket.timeout as exc:
        raise GeoMetadataFetchError("fetch_timeout", str(exc)) from exc
    except TimeoutError as exc:
        raise GeoMetadataFetchError("fetch_timeout", str(exc)) from exc
    except ssl.SSLError as exc:
        raise GeoMetadataFetchError("ssl_error", str(exc)) from exc
    except HTTPError as exc:
        if exc.code == 404:
            raise GeoMetadataFetchError("accession_not_found", str(exc)) from exc
        raise GeoMetadataFetchError("http_error", str(exc)) from exc
    except URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            raise GeoMetadataFetchError("ssl_error", str(reason)) from exc
        if isinstance(reason, TimeoutError | socket.timeout):
            raise GeoMetadataFetchError("fetch_timeout", str(reason)) from exc
        raise GeoMetadataFetchError("network_unavailable", str(reason)) from exc
    except OSError as exc:
        raise GeoMetadataFetchError("network_unavailable", str(exc)) from exc

    return payload.decode("utf-8", errors="replace")
