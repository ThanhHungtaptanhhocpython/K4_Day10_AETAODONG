from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from core.utils import now_utc, write_json

# Ngay "cu" dung de danh lua freshness check (stale date scenario).
STALE_DATE = "2000-01-01"
# Chuoi nhieu chen vao text_for_embedding (add noise scenario).
NOISE_STRING = " ##!!$$ zzqx random unrelated gibberish lorem ipsum 9f3k2 !!## "


def _rebuild_embedding_text(row: pd.Series) -> str:
    """Tao lai text_for_embedding tu cac field hien tai cua row."""
    title = str(row.get("title", ""))
    authors = str(row.get("authors_joined", ""))
    summary = str(row.get("summary", ""))
    return f"Title: {title} | Authors: {authors} | Summary: {summary}"


def corrupt_clean_dataframe(
    df: pd.DataFrame,
    output_log_path,
    target_paper_ids: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Simulate controlled data corruption tren clean dataframe.

    Ap it nhat 4 kich ban loi co chu dich (blank summary, stale date, add noise,
    duplicate) va LUON dam bao dung trung it nhat mot tai lieu nam trong frozen
    test set (qua ``target_paper_ids``), neu khong metrics se khong doi.

    Moi thay doi duoc ghi vao ``output_log_path`` (paper_id, type, before/after).
    """
    corrupted = df.copy().reset_index(drop=True)
    log: dict[str, Any] = {
        "generated_at": now_utc().isoformat(),
        "baseline_rows": int(len(df)),
        "scenarios": [],
        "affected_paper_ids": [],
    }
    affected: set[str] = set()

    # Uu tien nham vao cac paper co trong test set; neu khong co thi lay latest.
    targets = [pid for pid in (target_paper_ids or []) if pid in set(corrupted["paper_id"])]
    if not targets:
        # Fallback: chon cac paper moi nhat (test set cung uu tien latest).
        targets = (
            corrupted.sort_values("published", ascending=False)["paper_id"].head(4).tolist()
        )

    def _events() -> list[dict[str, Any]]:
        return log["scenarios"]

    # --- Kich ban 1: Blank Summary ---
    # Xoa summary cua target dau tien -> giam completeness, hong summary answers.
    if targets:
        pid = targets[0]
        mask = corrupted["paper_id"] == pid
        for idx in corrupted.index[mask]:
            before = str(corrupted.at[idx, "summary"])
            corrupted.at[idx, "summary"] = ""
            corrupted.at[idx, "summary_chars"] = 0
            corrupted.at[idx, "text_for_embedding"] = _rebuild_embedding_text(corrupted.loc[idx])
            _events().append(
                {
                    "type": "blank_summary",
                    "paper_id": pid,
                    "before": before[:120],
                    "after": "",
                }
            )
        affected.add(pid)

    # --- Kich ban 2: Stale Date ---
    # Lam cu ngay xuat ban cua target thu hai -> danh lua freshness check.
    if len(targets) > 1:
        pid = targets[1]
        mask = corrupted["paper_id"] == pid
        for idx in corrupted.index[mask]:
            before = str(corrupted.at[idx, "published"])
            corrupted.at[idx, "published"] = STALE_DATE
            # age_days tang vot -> vuot nguong freshness.
            corrupted.at[idx, "age_days"] = int(
                (now_utc().date() - pd.Timestamp(STALE_DATE).date()).days
            )
            _events().append(
                {
                    "type": "stale_date",
                    "paper_id": pid,
                    "before": before,
                    "after": STALE_DATE,
                }
            )
        affected.add(pid)

    # --- Kich ban 3: Add Noise ---
    # Chen ky tu nhieu vao text_for_embedding cua target thu ba -> hong retrieval.
    if len(targets) > 2:
        pid = targets[2]
        mask = corrupted["paper_id"] == pid
        for idx in corrupted.index[mask]:
            before = str(corrupted.at[idx, "text_for_embedding"])
            corrupted.at[idx, "text_for_embedding"] = NOISE_STRING + before + NOISE_STRING
            _events().append(
                {
                    "type": "add_noise",
                    "paper_id": pid,
                    "before": before[:120],
                    "after": (NOISE_STRING + before)[:120],
                }
            )
        affected.add(pid)

    # --- Kich ban 4: Duplicates ---
    # Nhan doi mot so target va giu nguyen paper_id -> pha uniqueness check.
    dup_targets = targets[: min(2, len(targets))]
    dup_rows = corrupted[corrupted["paper_id"].isin(dup_targets)].copy()
    if not dup_rows.empty:
        corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)
        for pid in dup_targets:
            _events().append(
                {
                    "type": "duplicate",
                    "paper_id": pid,
                    "before": "1 row",
                    "after": "2 rows",
                }
            )
            affected.add(pid)

    log["affected_paper_ids"] = sorted(affected)
    log["corrupted_rows"] = int(len(corrupted))
    log["scenario_count"] = len({e["type"] for e in log["scenarios"]})
    write_json(output_log_path, log)
    return corrupted
