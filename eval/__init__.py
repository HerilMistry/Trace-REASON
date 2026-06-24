"""
TRACE-Reason Multi-Model Evaluation Harness
============================================
Evaluates reasoning pipeline quality across free-tier LLM providers.

Modules:
  model_registry  – provider clients and unified chat() interface
  questions       – fixed evaluation questions + evidence fixtures
  evaluator       – backbone runner collecting raw outputs
  judge           – rotating LLM-as-judge scorer
  metrics         – claim extraction + hallucination rate computation
  leaderboard     – aggregation, composite score, heatmap, reports
"""

__version__ = "1.0.0"
__author__ = "TRACE-Reason Eval Harness"
