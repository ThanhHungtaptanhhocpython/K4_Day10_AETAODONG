from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, write_json


CROSSREF_API_URL = "https://api.crossref.org/works"
_RETRY_STATUS = {429, 500, 502, 503, 504}
_TAG_RE = re.compile(r"<[^>]+>")


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


def _strip_tags(value: str) -> str:
    return normalize_whitespace(_TAG_RE.sub(" ", value or ""))


def _format_date_parts(date_parts: list[list[int]] | None) -> str:
    if not date_parts or not date_parts[0]:
        return ""
    parts = date_parts[0]
    year = parts[0]
    month = parts[1] if len(parts) > 1 else 1
    day = parts[2] if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def _extract_date(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        payload = item.get(key) or {}
        formatted = _format_date_parts(payload.get("date-parts"))
        if formatted:
            return formatted
    return ""


def _extract_authors(item: dict[str, Any]) -> list[str]:
    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        name = normalize_whitespace(
            " ".join(part for part in [author.get("given"), author.get("family")] if part)
        )
        if not name and author.get("name"):
            name = normalize_whitespace(str(author["name"]))
        if name:
            authors.append(name)
    return authors


def _extract_categories(item: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    for subject in item.get("subject") or []:
        cleaned = normalize_whitespace(str(subject))
        if cleaned and cleaned not in categories:
            categories.append(cleaned)
    return categories


def _extract_pdf_url(item: dict[str, Any]) -> str:
    for link in item.get("link") or []:
        if not isinstance(link, dict):
            continue
        content_type = str(link.get("content-type") or "").lower()
        url = str(link.get("URL") or "").strip()
        if url and ("pdf" in content_type or url.lower().endswith(".pdf")):
            return url
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    message = payload.get("message") or {}
    items = message.get("items") or []
    records: list[PaperRecord] = []
    seen_ids: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        doi = normalize_whitespace(str(item.get("DOI") or ""))
        titles = item.get("title") or []
        title = _strip_tags(titles[0] if titles else "")
        summary = _strip_tags(str(item.get("abstract") or ""))
        if not doi or not title or not summary:
            continue

        paper_id = doi.lower()
        if paper_id in seen_ids:
            continue
        seen_ids.add(paper_id)

        authors = _extract_authors(item)
        categories = _extract_categories(item)
        published = _extract_date(
            item,
            "published-print",
            "published-online",
            "published",
            "issued",
            "created",
        )
        updated = _extract_date(item, "updated", "deposited", "created") or published
        abs_url = normalize_whitespace(str(item.get("URL") or f"https://doi.org/{doi}"))
        pdf_url = _extract_pdf_url(item)
        container = ""
        containers = item.get("container-title") or []
        if containers:
            container = _strip_tags(str(containers[0]))

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "uncategorized",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=container,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref API, luu raw response, parse thanh records."""
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "day10-data-observability-lab/0.1 (mailto:student@example.com)",
        "Accept": "application/json",
    }

    last_error: Exception | None = None
    payload: dict[str, Any] | None = None
    for attempt in range(5):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=60)
            if response.status_code in _RETRY_STATUS:
                wait_seconds = min(2**attempt, 16)
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            time.sleep(min(2**attempt, 16))

    if payload is None:
        raise RuntimeError(f"Failed to fetch Crossref records: {last_error}")

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    from core.utils import read_json

    payload = read_json(path)
    if isinstance(payload, dict):
        return parse_crossref_payload(payload)

    records: list[PaperRecord] = []
    for item in payload:
        records.append(
            PaperRecord(
                paper_id=str(item["paper_id"]),
                title=str(item.get("title") or ""),
                summary=str(item.get("summary") or ""),
                authors=list(item.get("authors") or []),
                categories=list(item.get("categories") or []),
                primary_category=str(item.get("primary_category") or "uncategorized"),
                published=str(item.get("published") or ""),
                updated=str(item.get("updated") or ""),
                abs_url=str(item.get("abs_url") or ""),
                pdf_url=str(item.get("pdf_url") or ""),
                comment=str(item.get("comment") or ""),
            )
        )
    return records
