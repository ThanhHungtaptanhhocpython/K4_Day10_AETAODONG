from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo evaluation set tu cleaned dataframe."""
    if len(df) < 4:
        raise ValueError("Need at least 4 cleaned papers to build an evaluation set.")

    selected = df.head(min(8, len(df))).copy()
    samples: list[dict[str, Any]] = []
    sample_id = 1

    for _, row in selected.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row["summary"])
        authors = str(row["authors_joined"])
        published = str(row["published"])
        categories = str(row["categories_joined"]) or str(row["primary_category"])

        question_specs = [
            (
                "summary",
                f"What is the paper '{title}' about?",
                first_sentence(summary),
            ),
            (
                "authors",
                f"Who authored the paper '{title}'?",
                authors,
            ),
            (
                "date",
                f"When was the paper '{title}' published?",
                published,
            ),
            (
                "categories",
                f"What categories describe the paper '{title}'?",
                categories,
            ),
        ]

        for question_type, question, ground_truth in question_specs:
            if not ground_truth or ground_truth.lower() in {"nan", "none"}:
                continue
            samples.append(
                {
                    "id": f"q{sample_id:03d}",
                    "question_type": question_type,
                    "question": question,
                    "ground_truth": ground_truth,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            sample_id += 1

    if len(samples) < 4:
        raise ValueError("Failed to build a useful evaluation set from the cleaned dataframe.")

    write_json(output_path, samples)
    return samples
