from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


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


import json
import time
import requests

def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records = []
    items = payload.get("message", {}).get("items", [])
    for item in items:
        paper_id = item.get("DOI", "")
        title = item.get("title", [""])[0] if item.get("title") else ""
        summary = item.get("abstract", "")
        
        authors = []
        for author in item.get("author", []):
            if "given" in author and "family" in author:
                authors.append(f"{author['given']} {author['family']}")
            elif "family" in author:
                authors.append(author["family"])
                
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""
        
        published = ""
        pub_date = item.get("published-print") or item.get("published-online") or item.get("created")
        if pub_date and "date-parts" in pub_date and pub_date["date-parts"]:
            parts = pub_date["date-parts"][0]
            if len(parts) == 3:
                published = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
            elif len(parts) == 2:
                published = f"{parts[0]:04d}-{parts[1]:02d}-01"
            elif len(parts) == 1:
                published = f"{parts[0]:04d}-01-01"
                
        updated = ""
        dep_date = item.get("deposited")
        if dep_date and "date-parts" in dep_date and dep_date["date-parts"]:
            parts = dep_date["date-parts"][0]
            if len(parts) == 3:
                updated = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
            
        abs_url = item.get("URL", "")
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break
                
        comment = ""
        
        record = PaperRecord(
            paper_id=paper_id,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment
        )
        records.append(record)
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results
    }
    url = "https://api.crossref.org/works"
    
    max_retries = 3
    payload = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to fetch from Crossref: {e}")
            time.sleep(2 ** attempt)
            
    if payload is None:
        raise RuntimeError("Failed to fetch from Crossref (payload is None)")
            
    # Save raw response
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    records = parse_crossref_payload(payload)
    
    # Save raw records
    records_dict = [vars(r) for r in records]
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump(records_dict, f, indent=2, ensure_ascii=False)
        
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**d) for d in data]
