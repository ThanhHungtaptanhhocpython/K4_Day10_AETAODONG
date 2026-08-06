from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(raw: str) -> str:
    """Crossref abstracts are JATS XML; strip tags and collapse whitespace."""
    if not raw:
        return ""
    # Drop JATS <jats:title>Abstract</jats:title> style headings and any XML tags.
    without_tags = re.sub(r"<[^>]+>", " ", raw)
    return normalize_whitespace(without_tags)


def _first_title(item: dict) -> str:
    titles = item.get("title") or []
    if not titles:
        return ""
    return normalize_whitespace(str(titles[0]))


def _authors(item: dict) -> list[str]:
    names: list[str] = []
    for author in item.get("author") or []:
        given = str(author.get("given", "")).strip()
        family = str(author.get("family", "")).strip()
        full = normalize_whitespace(f"{given} {family}")
        if not full:
            full = normalize_whitespace(str(author.get("name", "")))
        if full:
            names.append(full)
    return names


def _date_parts_to_iso(node: dict | None) -> str:
    """Convert a Crossref date node ({'date-parts': [[Y, M, D]]}) to an ISO date."""
    if not node:
        return ""
    parts = node.get("date-parts") or []
    if not parts or not parts[0]:
        return ""
    fields = parts[0]
    year = fields[0] if len(fields) > 0 and fields[0] else None
    if not year:
        return ""
    month = fields[1] if len(fields) > 1 and fields[1] else 1
    day = fields[2] if len(fields) > 2 and fields[2] else 1
    try:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except (TypeError, ValueError):
        return ""


def _published_date(item: dict) -> str:
    for key in ("published", "published-online", "published-print", "issued", "created"):
        iso = _date_parts_to_iso(item.get(key))
        if iso:
            return iso
    return ""


def _updated_date(item: dict) -> str:
    stamp = (item.get("indexed") or {}).get("date-time")
    if stamp:
        # Crossref timestamps look like "2024-05-01T12:00:00Z"; keep the date part.
        return normalize_whitespace(str(stamp)).split("T")[0]
    return _date_parts_to_iso(item.get("deposited"))


def _pdf_url(item: dict) -> str:
    for link in item.get("link") or []:
        content_type = str(link.get("content-type", "")).lower()
        if "pdf" in content_type:
            url = str(link.get("URL", "")).strip()
            if url:
                return url
    # Fall back to the first available link if no explicit PDF is present.
    links = item.get("link") or []
    if links:
        return str(links[0].get("URL", "")).strip()
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref /works payload into a list of PaperRecord.

    A record is only kept when it has a DOI, a title and a non-empty abstract,
    since those are the fields the downstream RAG pipeline relies on.
    """
    items = (payload.get("message") or {}).get("items") or []
    records: list[PaperRecord] = []
    for item in items:
        doi = normalize_whitespace(str(item.get("DOI", "")))
        title = _first_title(item)
        summary = _clean_abstract(str(item.get("abstract", "")))
        if not doi or not title or not summary:
            continue

        categories = [normalize_whitespace(str(c)) for c in (item.get("subject") or []) if str(c).strip()]
        primary_category = categories[0] if categories else "uncategorized"
        published = _published_date(item)
        if not published:
            continue

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=_authors(item),
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=_updated_date(item) or published,
                abs_url=str(item.get("URL", "")).strip(),
                pdf_url=_pdf_url(item),
                comment=normalize_whitespace(str(item.get("type", ""))),
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Call the Crossref API, persist the raw response and parsed records."""
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": (
            "DOI,title,abstract,author,subject,published,published-online,"
            "published-print,issued,created,indexed,deposited,URL,link,type"
        ),
    }
    headers = {
        # Crossref asks callers to identify themselves (the "polite pool").
        "User-Agent": "K4-Day10-DataPipeline/1.0 (mailto:student@example.com)",
    }

    payload: dict | None = None
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)
            if response.status_code in {429, 500, 502, 503, 504}:
                raise requests.HTTPError(f"Retryable status {response.status_code}")
            response.raise_for_status()
            payload = response.json()
            break
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            # Exponential backoff: 1s, 2s, 4s, 8s.
            time.sleep(2**attempt)
    if payload is None:
        raise RuntimeError(f"Failed to fetch Crossref data after retries: {last_error}")

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("Crossref returned no usable records (check query/filter).")

    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Read the parsed raw-records snapshot and map it back to PaperRecord."""
    payload = read_json(path)
    records: list[PaperRecord] = []
    for row in payload:
        records.append(
            PaperRecord(
                paper_id=str(row["paper_id"]),
                title=str(row["title"]),
                summary=str(row["summary"]),
                authors=list(row.get("authors") or []),
                categories=list(row.get("categories") or []),
                primary_category=str(row.get("primary_category", "uncategorized")),
                published=str(row.get("published", "")),
                updated=str(row.get("updated", "")),
                abs_url=str(row.get("abs_url", "")),
                pdf_url=str(row.get("pdf_url", "")),
                comment=str(row.get("comment", "")),
            )
        )
    return records
