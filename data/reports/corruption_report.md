# Phase 2: Corruption and Repair Comparison Report

## Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Hit Rate | 1.0000 | 0.6000 | 1.0000 |
| Token F1 | 0.4324 | 0.2501 | 0.4324 |
| Judge Accuracy | 0.3333 | 0.2000 | 0.3333 |
| Mean Judge Score | 2.3333 | 1.8000 | 2.3333 |

## Quality & Freshness (Corrupted)
- Quality Passed: False (Short summaries: 1, Empty titles: 0, Duplicates: 1)
- Is Fresh: False (Stale rows: 1)

## Quality & Freshness (Repaired)
- Quality Passed: True (Short summaries: 0, Empty titles: 0, Duplicates: 0)
- Is Fresh: True (Stale rows: 0)
