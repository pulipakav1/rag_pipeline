# Sample Results

## Run Context

- Model: `claude-sonnet-4-20250514`
- Embeddings: `multi-qa-MiniLM-L6-cos-v1`
- Retrieval: Top-K `5`
- Eval: enabled (`faithfulness`, `relevance`, `retrieval_precision`)

## Example Query

**Question**

`What is fairness and bias in LLMs according to this study?`

## Retrieved Chunks

1. `llm_fairness_drift_study.pdf` - fairness is multidimensional; weak correlation between different fairness metrics.
2. `llm_fairness_drift_study.pdf` - sentiment and toxicity improvements do not always reduce stereotype bias.
3. `llm_fairness_drift_study.pdf` - fairness changes over time and across model updates.
4. `llm_fairness_drift_study.pdf` - evaluation uses multiple complementary metrics (not a single score).
5. `llm_fairness_drift_study.pdf` - demographic parity / equalized odds referenced in supervised settings.

## Generated Answer (excerpt)

The study treats fairness and bias in LLMs as multidimensional properties, not a single number. It reports that gains in safety-oriented indicators (for example toxicity) do not consistently imply improvements in stereotype-related bias, so these dimensions should be tracked separately. The paper also frames fairness as dynamic across model revisions and recommends using multiple complementary metrics for evaluation.

Sources: `llm_fairness_drift_study.pdf`

## Eval Scores

- Faithfulness: **0.91** (**91%**)
- Answer Relevance: **0.88** (**88%**)
- Retrieval Precision: **0.84** (**84%**)
- Overall: **0.877** (**87.7%**)

## Notes

- Scores vary with chunking settings, Top-K, and question phrasing.
- Re-ingest after changing chunk or embedding defaults for consistent comparisons.
