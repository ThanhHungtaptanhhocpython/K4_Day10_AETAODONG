# Phase 1 - Baseline Report

_Generated at 2026-08-06T08:44:50.909364+00:00_

## Data Source

- **source_api**: Crossref REST API
- **source_query**: agentic retrieval augmented generation large language model
- **source_filter**: from-pub-date:2026-02-07,has-abstract:true
- **records_fetched**: 24
- **records_clean**: 24
- **embedding_model**: sentence-transformers/all-MiniLM-L6-v2
- **collection**: papers-baseline

## Evaluation Metrics

| Metric | Value |
| --- | --- |
| samples | 24 |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 1.0000 |
| judge_accuracy | 1.0000 |
| mean_judge_score | 5 |

## Data Quality

- Overall: **PASS** (6/6 checks passed)

| Check | Result | Details |
| --- | --- | --- |
| row_count | PASS | rows=24, min_rows=5 |
| paper_id_not_null | PASS | null_paper_ids=0 |
| paper_id_unique | PASS | duplicate_paper_ids=0 |
| title_not_null | PASS | null_titles=0 |
| summary_min_length | PASS | short_summaries=0, min_chars=100 |
| freshness_age_days | PASS | stale_rows=0, threshold_days=180 |

## Freshness

- Status: **FRESH**
- Latest published: 2026-08-01
- Oldest published: 2026-02-12
- Stale rows: 0 / 24 (threshold 180 days)
- Max age (days): 175

