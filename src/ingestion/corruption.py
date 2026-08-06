from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from core.utils import write_json


def _rebuild_text_for_embedding(df: pd.DataFrame) -> pd.DataFrame:
    def build_text(row: pd.Series) -> str:
        parts = [
            f"Title: {row.get('title', '')}",
            f"Authors: {row.get('authors_joined', '')}" if row.get("authors_joined") else "",
            f"Categories: {row.get('categories_joined', '')}" if row.get("categories_joined") else "",
            f"Published: {row.get('published', '')}" if row.get("published") else "",
            f"Summary: {row.get('summary', '')}",
        ]
        return "\n".join(part for part in parts if part)

    out = df.copy()
    out["text_for_embedding"] = out.apply(build_text, axis=1)
    if "summary" in out.columns:
        out["summary_chars"] = out["summary"].astype(str).str.len()
    return out


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate nhieu dang data corruption."""
    if df.empty:
        raise ValueError("Cannot corrupt an empty dataframe.")

    working = df.copy().reset_index(drop=True)
    log: dict[str, object] = {"actions": [], "original_rows": int(len(working))}

    # 1. Drop some latest records.
    drop_n = min(3, max(1, len(working) // 4))
    dropped_ids = working.head(drop_n)["paper_id"].tolist()
    working = working.iloc[drop_n:].reset_index(drop=True)
    log["actions"].append({"type": "drop_latest_records", "count": drop_n, "paper_ids": dropped_ids})

    if working.empty:
        raise ValueError("Corruption removed all rows; adjust drop count.")

    # 2. Blank summary on some rows.
    blank_n = min(2, len(working))
    blank_ids = working.head(blank_n)["paper_id"].tolist()
    working.loc[working.index[:blank_n], "summary"] = ""
    log["actions"].append({"type": "blank_summary", "count": blank_n, "paper_ids": blank_ids})

    # 3. Inject noise into text.
    noise_idx = min(blank_n, len(working) - 1)
    noise_id = working.iloc[noise_idx]["paper_id"]
    working.at[working.index[noise_idx], "summary"] = (
        str(working.at[working.index[noise_idx], "summary"])
        + " [NOISE] lorem ipsum dolor sit amet random tokens xyz123"
    )
    log["actions"].append({"type": "inject_noise", "paper_id": noise_id})

    # 4. Truncate titles.
    truncate_n = min(2, len(working))
    truncate_ids = working.tail(truncate_n)["paper_id"].tolist()
    for idx in working.index[-truncate_n:]:
        title = str(working.at[idx, "title"])
        working.at[idx, "title"] = title[: max(8, len(title) // 3)]
    log["actions"].append({"type": "truncate_title", "count": truncate_n, "paper_ids": truncate_ids})

    # 5. Make publication dates stale.
    stale_n = min(3, len(working))
    stale_ids = working.head(stale_n)["paper_id"].tolist()
    stale_date = (datetime.now(UTC) - timedelta(days=800)).date().isoformat()
    for idx in working.index[:stale_n]:
        working.at[idx, "published"] = stale_date
        working.at[idx, "age_days"] = 800
    log["actions"].append({"type": "stale_published_date", "count": stale_n, "paper_ids": stale_ids, "published": stale_date})

    # 6. Add duplicate rows.
    duplicate_n = min(2, len(working))
    duplicates = working.head(duplicate_n).copy()
    working = pd.concat([working, duplicates], ignore_index=True)
    log["actions"].append(
        {
            "type": "add_duplicates",
            "count": duplicate_n,
            "paper_ids": duplicates["paper_id"].tolist(),
        }
    )

    # 7. Rebuild embedding text and age_days where possible.
    working = _rebuild_text_for_embedding(working)
    if "published" in working.columns:
        published = pd.to_datetime(working["published"], errors="coerce", utc=True)
        today = datetime.now(UTC).date()
        working["age_days"] = published.apply(
            lambda value: (today - value.date()).days if pd.notna(value) else None
        )

    log["corrupted_rows"] = int(len(working))
    write_json(Path(output_log_path), log)
    return working
