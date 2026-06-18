# TRACE-Reason

Traceable Reasoning for Enzyme Function Interpretation using Grounded Biological Evidence

## Overview

TRACE-Reason is a research system that evaluates whether grounded biological evidence improves LLM-based enzyme reasoning and reduces hallucinations. The system integrates structured enzyme metadata, protein embeddings, mutation analysis, and multi-node reasoning graphs to generate traceable, faithful explanations of enzyme function.

## Core Hypothesis

**Grounded evidence improves biological reasoning quality and reduces hallucination compared with standard LLM prompting.**

## Benchmark Dataset

10 enzyme drug targets for neurological diseases:

| Class | Enzymes |
|-------|---------|
| Kinase | LRRK2, GSK3B, CDK5 |
| Protease | BACE1, CASP3 |
| HDAC | HDAC6 |
| PDE | PDE4D |
| Oxidoreductase | MAOB |
| Cholinesterase | ACHE, BCHE |

## Pipeline Architecture

```
Dataset → ESM2 Embeddings → Mutation Analysis → Evidence Construction
    ↓
LangGraph Reasoning (6-node) → Grounded Explanation
    ↓
Evaluation Metrics → Experiment Results → Publication-Ready Outputs
```

## Project Structure

```
trace-reason/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── enzymes.json
│   ├── benchmark_enzymes.json
│   ├── mutations.csv
│   └── eval_questions.json
├── configs/
│   ├── llm.yaml
│   ├── reasoning.yaml
│   └── embedding.yaml
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   ├── embeddings/
│   ├── evidence/
│   ├── reasoning/
│   ├── llm/
│   ├── evaluation/
│   └── api/
├── outputs/
│   ├── embeddings/
│   ├── traces/
│   ├── experiments/
│   ├── figures/
│   └── reports/
└── tests/
```

## Experiments

### Experiment 1: Baseline
Standard LLM with enzyme metadata only (no grounding).

### Experiment 2: TRACE-Reason
Full evidence package with 6-node reasoning pipeline.

### Experiment 3: Mutation Ablation
Measure impact of mutation evidence.

### Experiment 4: Node Ablation
Remove mutation, disease, and kinetic nodes individually.

## Evaluation Metrics

- **Faithfulness**: supported_claims / total_claims
- **Hallucination Rate**: unsupported_claims / total_claims
- **Evidence Utilization**: used_evidence / available_evidence
- **Trace Completeness**: completed_nodes / total_nodes
- **Consistency**: agreement across 5 runs
- **Grounding Score**: 0.4 × Faithfulness - 0.3 × Evidence Utilization - 0.3 × (1 - Hallucination Rate)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Generate benchmark and mutations
python scripts/prepare_data.py

# Run baseline experiment
python scripts/run_baseline.py

# Run TRACE-Reason experiment
python scripts/run_trace_reason.py

# Generate figures and report
python scripts/generate_report.py
```

## Outputs

- `outputs/experiments/` - CSV files with raw results
- `outputs/figures/` - PNG plots
- `outputs/reports/` - Markdown reports with tables

## Publication

The system generates paper-ready tables, figures, and reports suitable for workshop papers, thesis chapters, or conference submissions.
