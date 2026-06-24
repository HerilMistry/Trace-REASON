"""
judge.py
========
LLM-as-a-judge scorer for TRACE-Reason evaluation harness.

For each (question, evidence, model_output) triple, a *separate* judge model
(chosen by rotating away from the backbone's provider) scores the output on:
  - Faithfulness  (1-5): grounding in supplied evidence
  - Correctness   (1-5): mechanistic biological accuracy
  - Completeness  (1-5): coverage of all question parts

The judge is instructed to:
  1. Reason step by step BEFORE scoring.
  2. Output ONLY valid JSON at the end.
  3. Explicitly penalise unsupported / hallucinated claims.

If the primary judge fails, the harness retries with the next available
judge model.  Temperature is fixed at 0.0 for reproducibility.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from eval.model_registry import chat, get_judge_candidates, ALL_MODEL_NAMES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class JudgeResult:
    question_id: str
    backbone_model: str
    judge_model: str
    faithfulness: int       # 1-5
    correctness: int        # 1-5
    completeness: int       # 1-5
    reasoning: str          # one-sentence summary from the judge
    unsupported_claims: List[str] = field(default_factory=list)
    judge_error: Optional[str] = None  # set if judge call failed

    @property
    def mean_score(self) -> float:
        return (self.faithfulness + self.correctness + self.completeness) / 3.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "backbone_model": self.backbone_model,
            "judge_model": self.judge_model,
            "faithfulness": self.faithfulness,
            "correctness": self.correctness,
            "completeness": self.completeness,
            "mean_score": round(self.mean_score, 4),
            "reasoning": self.reasoning,
            "unsupported_claims": self.unsupported_claims,
            "judge_error": self.judge_error,
        }


# ---------------------------------------------------------------------------
# Judge prompt
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM_PROMPT = """\
You are a rigorous scientific evaluator specialising in molecular biology, \
enzyme biochemistry, and neuroscience drug discovery.

Your task is to evaluate an AI model's response to a biology reasoning question.
You must be STRICT and ACCURATE.  Do NOT give high scores for vague or generic answers.

IMPORTANT RULES:
- Read the EVIDENCE carefully.  Any claim in the response that cannot be traced \
back to the supplied evidence or well-established molecular biology must be \
flagged as unsupported.
- Penalise hallucinated kinetic values, protein names, drug names, or variant \
notations that are NOT present in the evidence.
- Score 1 if the output is fundamentally wrong or mostly hallucinated.
- Score 5 only for outputs that are precise, grounded, and comprehensive.
"""

_JUDGE_USER_TEMPLATE = """\
=== EVALUATION TASK ===

QUESTION:
{question}

SUPPLIED EVIDENCE:
{evidence}

MODEL OUTPUT TO EVALUATE:
{model_output}

=== SCORING RUBRIC ===

Score each criterion from 1 to 5:

FAITHFULNESS (1-5):
  1 = Multiple invented facts, contradicts evidence
  2 = Some grounding but major unsupported claims
  3 = Mostly grounded, minor unsupported details
  4 = Well-grounded, only very minor gaps
  5 = Every claim traceable to evidence, nothing invented

CORRECTNESS (1-5):
  1 = Fundamental mechanistic errors
  2 = Mostly wrong or confusing mechanisms
  3 = Broadly correct with some inaccuracies
  4 = Mechanistically accurate with minor imprecision
  5 = Precise, technically correct molecular mechanisms

COMPLETENESS (1-5):
  1 = Addresses < 25% of the question
  2 = Addresses ~50% of the question
  3 = Addresses ~75%, misses some key aspects
  4 = Addresses ~90%, minor omissions
  5 = Fully addresses all parts of the question

=== YOUR EVALUATION ===

Think step by step:

Step 1 — Faithfulness: Identify any claims that cannot be grounded in the \
supplied evidence.  List them explicitly.

Step 2 — Correctness: Check the biological mechanisms stated.  Are they \
mechanistically accurate for this enzyme/disease?

Step 3 — Correctness: Assess which parts of the question were answered \
thoroughly and which were missed.

Step 4 — Assign integer scores (1-5) for each criterion.

After your step-by-step reasoning, output ONLY the following JSON block \
(no other text after it):

```json
{{
  "faithfulness": <integer 1-5>,
  "correctness": <integer 1-5>,
  "completeness": <integer 1-5>,
  "reasoning": "<one sentence summarising your evaluation>",
  "unsupported_claims": ["<claim1>", "<claim2>"]
}}
```
"""


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract the first valid JSON object from judge response text."""
    # Try direct parse
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from a ```json ... ``` block
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the last { ... } block
    brace_start = text.rfind("{")
    brace_end   = text.rfind("}") + 1
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end])
        except json.JSONDecodeError:
            pass

    return None


def _clamp(val: Any, lo: int = 1, hi: int = 5) -> int:
    """Clamp a value to [lo, hi] and cast to int."""
    try:
        return max(lo, min(hi, int(val)))
    except (TypeError, ValueError):
        return 3  # neutral fallback


# ---------------------------------------------------------------------------
# Core judge call
# ---------------------------------------------------------------------------

def _call_judge(
    judge_model: str,
    question: str,
    evidence_summary: str,
    model_output: str,
    temperature: float = 0.0,
    max_tokens: int = 1500,
) -> Optional[Dict[str, Any]]:
    """
    Call a single judge model and parse its JSON response.
    Returns the parsed dict, or None if parsing fails.
    """
    messages = [
        {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _JUDGE_USER_TEMPLATE.format(
                question=question,
                evidence=evidence_summary,
                model_output=model_output,
            ),
        },
    ]
    response = chat(
        judge_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if not response.success:
        logger.warning("Judge model %s failed: %s", judge_model, response.error)
        return None

    parsed = _extract_json(response.content)
    if parsed is None:
        logger.warning("Judge %s returned unparseable response:\n%s", judge_model, response.content[:500])
    return parsed


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

# Round-robin state (per-backbone index into judge candidates)
_judge_rotation_index: Dict[str, int] = {}


def score(
    question_id: str,
    question_text: str,
    evidence_summary: str,
    model_output: str,
    backbone_model: str,
    max_retries: int = 3,
    temperature: float = 0.0,
) -> JudgeResult:
    """
    Score a model output using a rotating judge.

    The judge is selected from a DIFFERENT provider than the backbone model.
    If the primary judge fails, retries with the next candidates.

    Args:
        question_id:      Question identifier (e.g. "Q1")
        question_text:    Full question text
        evidence_summary: Compact string of the evidence package
        model_output:     The backbone model's text output to score
        backbone_model:   Registry key of the backbone (for judge rotation)
        max_retries:      How many judges to try before giving up
        temperature:      Judge call temperature (default 0.0)

    Returns:
        JudgeResult (with judge_error set if all attempts failed)
    """
    candidates = get_judge_candidates(backbone_model)

    # If no output, return a zero score immediately
    if not model_output or not model_output.strip():
        return JudgeResult(
            question_id=question_id,
            backbone_model=backbone_model,
            judge_model="N/A",
            faithfulness=1,
            correctness=1,
            completeness=1,
            reasoning="No output from backbone model.",
            judge_error="Empty backbone output",
        )

    # Pick starting position via round-robin
    start = _judge_rotation_index.get(backbone_model, 0)
    _judge_rotation_index[backbone_model] = (start + 1) % max(len(candidates), 1)

    for attempt in range(min(max_retries, len(candidates))):
        judge_model = candidates[(start + attempt) % len(candidates)]
        logger.info(
            "  [judge] %s → scored by %s (attempt %d)",
            backbone_model, judge_model, attempt + 1,
        )
        parsed = _call_judge(
            judge_model=judge_model,
            question=question_text,
            evidence_summary=evidence_summary,
            model_output=model_output,
            temperature=temperature,
        )
        if parsed is not None:
            return JudgeResult(
                question_id=question_id,
                backbone_model=backbone_model,
                judge_model=judge_model,
                faithfulness=_clamp(parsed.get("faithfulness", 3)),
                correctness=_clamp(parsed.get("correctness", 3)),
                completeness=_clamp(parsed.get("completeness", 3)),
                reasoning=str(parsed.get("reasoning", "")),
                unsupported_claims=list(parsed.get("unsupported_claims", [])),
            )

    # All judges failed — return a neutral fallback
    logger.error("All %d judge attempts failed for backbone %s / question %s",
                 max_retries, backbone_model, question_id)
    return JudgeResult(
        question_id=question_id,
        backbone_model=backbone_model,
        judge_model="FAILED",
        faithfulness=1,
        correctness=1,
        completeness=1,
        reasoning="Judge evaluation failed for all candidates.",
        judge_error=f"All {max_retries} judge attempts failed",
    )


def batch_score(
    eval_records: List[Any],  # List[EvalRecord] from evaluator.py
    max_retries: int = 3,
    temperature: float = 0.0,
) -> List[JudgeResult]:
    """
    Score a batch of EvalRecords, returning a parallel list of JudgeResults.
    Skips records where the backbone call failed (assigns 1/1/1).
    """
    from eval.questions import QUESTION_BY_ID  # lazy import to avoid circular

    results: List[JudgeResult] = []
    for rec in eval_records:
        q = QUESTION_BY_ID.get(rec.question_id)
        evidence_summary = q.evidence_summary() if q else "Evidence unavailable."

        result = score(
            question_id=rec.question_id,
            question_text=rec.question_text,
            evidence_summary=evidence_summary,
            model_output=rec.model_output,
            backbone_model=rec.model_name,
            max_retries=max_retries,
            temperature=temperature,
        )
        results.append(result)
    return results
