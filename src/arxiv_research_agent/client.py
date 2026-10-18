from __future__ import annotations

from dataclasses import asdict, dataclass
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"
MAX_RESULTS = 5
MAX_QUERY_LENGTH = 200
REQUEST_TIMEOUT_SECONDS = 12
MAX_RESPONSE_BYTES = 2_000_000


class ArxivSearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Paper:
    title: str
    abstract: str
    url: str
    published: str
    updated: str
    authors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["authors"] = list(self.authors)
        return data


def _normalized_text(value: str | None) -> str:
    return " ".join((value or "").split())


def _canonical_abs_url(raw_url: str) -> str | None:
    parsed = urllib.parse.urlsplit(raw_url.strip())
    if parsed.hostname not in {"arxiv.org", "www.arxiv.org"}:
        return None
    if not parsed.path.startswith("/abs/"):
        return None
    return urllib.parse.urlunsplit(("https", "arxiv.org", parsed.path, "", ""))


def _parse_atom(payload: bytes) -> list[Paper]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ArxivSearchError("arXiv returned malformed Atom XML") from error

    papers: list[Paper] = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry")[:MAX_RESULTS]:
        title = _normalized_text(entry.findtext(f"{{{ATOM_NS}}}title"))
        abstract = _normalized_text(entry.findtext(f"{{{ATOM_NS}}}summary"))
        url = _canonical_abs_url(entry.findtext(f"{{{ATOM_NS}}}id") or "")
        authors = tuple(
            name
            for author in entry.findall(f"{{{ATOM_NS}}}author")
            if (name := _normalized_text(author.findtext(f"{{{ATOM_NS}}}name")))
        )
        if not title or not abstract or not url:
            continue
        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                url=url,
                published=_normalized_text(entry.findtext(f"{{{ATOM_NS}}}published"))[:10],
                updated=_normalized_text(entry.findtext(f"{{{ATOM_NS}}}updated"))[:10],
                authors=authors,
            )
        )
    return papers


def search_papers(query: str) -> list[Paper]:
    query = query.strip()
    if not query or len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"query must contain 1 to {MAX_QUERY_LENGTH} characters")

    params = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": MAX_RESULTS,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "charan-arxiv-research-agent/0.1 (research discovery tool)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ArxivSearchError(f"arXiv request failed: {type(error).__name__}") from error
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ArxivSearchError("arXiv response exceeded the 2 MB safety limit")
    return _parse_atom(payload)
