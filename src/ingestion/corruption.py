from __future__ import annotations

import pandas as pd


import json

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    if df.empty:
        return df
        
    corrupted_df = df.copy()
    logs = []
    
    # 1. Drop a few latest records (Mô phỏng lỗi đường truyền bị rớt mất gói tin cuối cùng)
    if len(corrupted_df) > 5:
        dropped = corrupted_df.head(2)
        corrupted_df = corrupted_df.iloc[2:].reset_index(drop=True)
        logs.append(f"Dropped {len(dropped)} latest records.")
        
    # 2. Blank summary (Mô phỏng lỗi schema migration hoặc API bị chặn không cho quét summary)
    if len(corrupted_df) > 1:
        idx = 0
        corrupted_df.loc[idx, "summary"] = ""
        logs.append(f"Blanked summary for paper {corrupted_df.loc[idx, 'paper_id']}.")
        
    # 3. Inject noise (Mô phỏng lỗi encoding text hoặc bị chèn mã độc HTML)
    if len(corrupted_df) > 2:
        idx = 1
        corrupted_df.loc[idx, "summary"] = "NOISE_123_INVALID " + str(corrupted_df.loc[idx, "summary"])
        logs.append(f"Injected noise into summary of paper {corrupted_df.loc[idx, 'paper_id']}.")
        
    # 4. Truncate title (Mô phỏng lỗi DB giới hạn VARCHAR quá nhỏ)
    if len(corrupted_df) > 3:
        idx = 2
        corrupted_df.loc[idx, "title"] = str(corrupted_df.loc[idx, "title"])[:5]
        logs.append(f"Truncated title of paper {corrupted_df.loc[idx, 'paper_id']}.")
        
    # 5. Stale date (Mô phỏng cronjob crawl dữ liệu bị treo không cập nhật ngày mới)
    if len(corrupted_df) > 4:
        idx = 3
        corrupted_df.loc[idx, "published"] = "1999-01-01"
        corrupted_df.loc[idx, "age_days"] = 9999
        logs.append(f"Made published date stale for paper {corrupted_df.loc[idx, 'paper_id']}.")
        
    # 6. Duplicate row (Mô phỏng lỗi retry request nhiều lần dẫn đến insert trùng)
    if len(corrupted_df) > 5:
        idx = 4
        dup_row = corrupted_df.iloc[[idx]].copy()
        corrupted_df = pd.concat([corrupted_df, dup_row], ignore_index=True)
        logs.append(f"Duplicated paper {corrupted_df.loc[idx, 'paper_id']}.")
        
    corrupted_df["text_for_embedding"] = "Title: " + corrupted_df["title"].fillna("") + "\n\nAbstract: " + corrupted_df["summary"].fillna("")
    
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, "w", encoding="utf-8") as f:
        json.dump({"actions": logs}, f, indent=2, ensure_ascii=False)
        
    return corrupted_df
