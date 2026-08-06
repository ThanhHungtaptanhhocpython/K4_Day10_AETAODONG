from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


import re

def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
        
    data = [vars(r) for r in records]
    df = pd.DataFrame(data)
    
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    
    df["title"] = df["title"].fillna("").str.strip()
    df["summary"] = df["summary"].fillna("").str.strip()
    
    df["summary"] = df["summary"].apply(lambda x: re.sub(r'<[^>]+>', '', str(x)).strip())
    df["title"] = df["title"].apply(lambda x: re.sub(r'<[^>]+>', '', str(x)).strip())
    
    df = df[df["title"].str.len() > 0]
    df = df[df["summary"].str.len() > 20]
    
    df["authors_joined"] = df["authors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    df["categories_joined"] = df["categories"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    df["summary_chars"] = df["summary"].str.len()
    
    df["text_for_embedding"] = "Title: " + df["title"] + "\n\nAbstract: " + df["summary"]
    
    df["published_dt"] = pd.to_datetime(df["published"], errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["published_dt"])
    
    run_date_naive = run_date.replace(tzinfo=None)
    df["age_days"] = (run_date_naive - df["published_dt"]).dt.days
    df["age_days"] = df["age_days"].clip(lower=0)
    
    df["published"] = df["published_dt"].dt.strftime("%Y-%m-%d")
    df = df.drop(columns=["published_dt"])
    
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    
    return df
