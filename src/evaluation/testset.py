from __future__ import annotations

from typing import Any

import pandas as pd


import json
import uuid

def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if df.empty:
        return []
    
    sample_df = df.head(5)
    
    test_set = []
    
    for _, row in sample_df.iterrows():
        paper_id = row["paper_id"]
        title = row["title"]
        authors = row["authors_joined"]
        published = row["published"]
        categories = row["categories_joined"]
        
        test_set.append({
            "id": str(uuid.uuid4()),
            "question_type": "summary",
            "question": f"What is the main topic or summary of the paper '{title}'?",
            "ground_truth": row["summary"],
            "ground_truth_doc_ids": [paper_id]
        })
        
        if authors:
            test_set.append({
                "id": str(uuid.uuid4()),
                "question_type": "authors",
                "question": f"Who are the authors of the paper '{title}'?",
                "ground_truth": authors,
                "ground_truth_doc_ids": [paper_id]
            })
        
        if published:
            test_set.append({
                "id": str(uuid.uuid4()),
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id]
            })
            
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)
        
    return test_set
