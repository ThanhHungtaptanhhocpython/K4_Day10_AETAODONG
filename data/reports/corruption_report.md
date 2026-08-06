# Corruption Comparison Report

## Metrics comparison

| Metric | Baseline | Corrupted | Repaired | Delta corrupted | Delta repaired |
| --- | ---: | ---: | ---: | ---: | ---: |
| retrieval_hit_rate | 1.0 | 0.625 | 1.0 | -0.3750 | +0.0000 |
| mean_token_f1 | 0.75 | 0.3238449972662657 | 0.75 | -0.4262 | +0.0000 |
| judge_accuracy | 0.75 | 0.3125 | 0.75 | -0.4375 | +0.0000 |
| mean_judge_score | 4 | 2.375 | 4 | -1.6250 | +0.0000 |

## Data quality

- Corrupted success: False (failed: paper_id_unique, summary_min_length, freshness_threshold)
- Repaired success: True (failed: none)

## Freshness

- Corrupted stale rows: 5 / 23 (is_fresh=False)
- Repaired stale rows: 0 / 24 (is_fresh=True)

## Interpretation

- Corruption is expected to reduce retrieval/answer quality and increase quality/freshness failures.
- Repair from raw source should restore metrics closer to the baseline and clear intentional data defects.
