from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

# Frozen Evaluation Set: bo cau hoi phai duoc chot va giu co dinh de so sanh
# cong bang chat luong RAG giua 3 trang thai baseline / corrupted / repaired.
MIN_DOCUMENTS = 4
MAX_PAPERS = 8


def _summary_answer(row: pd.Series) -> tuple[str, str] | None:
    if not str(row["summary"]).strip():
        return None
    question = f"What is the paper titled '{row['title']}' about?"
    return question, first_sentence(str(row["summary"]))


def _authors_answer(row: pd.Series) -> tuple[str, str] | None:
    authors = str(row["authors_joined"]).strip()
    if not authors:
        return None
    question = f"Who authored the paper titled '{row['title']}'?"
    return question, authors


def _date_answer(row: pd.Series) -> tuple[str, str] | None:
    published = str(row["published"]).strip()
    if not published:
        return None
    question = f"When was the paper titled '{row['title']}' published on?"
    return question, published


def _categories_answer(row: pd.Series) -> tuple[str, str] | None:
    categories = str(row["categories_joined"]).strip()
    if not categories:
        return None
    question = f"What categories does the paper titled '{row['title']}' belong to?"
    return question, categories


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a frozen factual evaluation set from the cleaned dataframe.

    Every question is answerable directly from the clean data, and its
    ``ground_truth_doc_ids`` points at the ``paper_id`` that holds the answer.
    Question phrasing is aligned with ``retrieval.qa._extract_answer`` so the
    ground truth is exactly what a correct retrieval + extraction returns.
    Schema per sample: id, question_type, question, ground_truth, ground_truth_doc_ids.
    """
    if len(df) < MIN_DOCUMENTS:
        raise ValueError(
            f"Need at least {MIN_DOCUMENTS} documents to build a test set, got {len(df)}."
        )

    # Pick representative papers: prefer ones with authors and categories present.
    scored = df.copy()
    scored["_completeness"] = (
        (scored["authors_joined"].astype(str).str.len() > 0).astype(int)
        + (scored["categories_joined"].astype(str).str.len() > 0).astype(int)
    )
    selected = scored.sort_values(
        by=["_completeness", "published"], ascending=[False, False]
    ).head(MAX_PAPERS)

    builders = (_summary_answer, _authors_answer, _date_answer, _categories_answer)
    test_set: list[dict[str, Any]] = []
    for _, row in selected.iterrows():
        for builder in builders:
            result = builder(row)
            if result is None:
                continue
            question, ground_truth = result
            test_set.append(
                {
                    "id": f"q{len(test_set) + 1}",
                    "question_type": "factual",
                    "question": question,
                    "ground_truth": ground_truth,
                    "ground_truth_doc_ids": [row["paper_id"]],
                }
            )

    if len(test_set) < 5:
        raise ValueError(
            f"Frozen eval set needs at least 5 questions, only built {len(test_set)}."
        )

    write_json(output_path, test_set)
    return test_set
