"""
evaluator.py
============
Backbone model runner for the TRACE-Reason multi-model evaluation harness.

Two evaluation modes are supported:
  pipeline  (default): Runs the full 6-node ReasoningPipeline and extracts
                        the final_explanation as the scored output.
  direct:              Asks the backbone model a single direct question,
                        bypassing the multi-step pipeline.

For each (backbone model × question) pair the evaluator:
  1. Builds an EvidencePackage from the question fixture.
  2. Calls the backbone (via model_registry) using a ReasoningPipeline adapter.
  3. Records latency, token count, raw output, and pipeline trace.
  4. Catches all API/runtime exceptions and marks the record as failed.

Temperature is fixed at 0.0 for ALL backbone calls.
"""

from __future__ import annotations

import json
import logging
import sys
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# Ensure project root is importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from eval.model_registry import chat, ALL_MODEL_NAMES, ChatResponse
from eval.questions import EvalQuestion, QUESTION_BANK, get_questions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EvalRecord — one (backbone model × question) result
# ---------------------------------------------------------------------------

@dataclass
class EvalRecord:
    question_id: str
    question_text: str
    enzyme: str
    mutation: Optional[str]
    model_name: str           # registry key e.g. "groq/llama-3.3-70b-versatile"
    model_provider: str
    mode: str                 # "pipeline" | "direct"

    model_output: str = ""    # final scored text
    pipeline_trace: Optional[Dict[str, Any]] = None  # full ReasoningTrace as dict

    latency_seconds: float = 0.0
    token_count: int = 0
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "enzyme": self.enzyme,
            "mutation": self.mutation,
            "model_name": self.model_name,
            "model_provider": self.model_provider,
            "mode": self.mode,
            "model_output": self.model_output,
            "latency_seconds": round(self.latency_seconds, 3),
            "token_count": self.token_count,
            "success": self.success,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# LLMProvider adapter — wraps model_registry.chat() to satisfy
# the interface expected by src.reasoning.ReasoningPipeline
# ---------------------------------------------------------------------------

class _RegistryLLMAdapter:
    """
    Adapts the model_registry's stateless chat() function into the
    LLMProvider interface (query / structured_query) expected by
    src.reasoning.ReasoningPipeline.
    """

    def __init__(self, model_name: str, temperature: float = 0.0, max_tokens: int = 2048):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._total_tokens: int = 0
        self._total_latency: float = 0.0

    # --- LLMProvider protocol ------------------------------------------

    def query(self, prompt: str, **kwargs) -> str:
        resp = chat(
            self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        self._total_tokens   += resp.token_count
        self._total_latency  += resp.latency_seconds
        if not resp.success:
            raise RuntimeError(f"API error from {self.model_name}: {resp.error}")
        return resp.content

    def structured_query(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        schema_str = json.dumps(schema, indent=2)
        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with ONLY valid JSON that exactly matches "
            f"this schema (no explanations, no markdown, no extra text):\n"
            f"{schema_str}"
        )
        content = self.query(full_prompt)
        return _safe_json_parse(content)


def _safe_json_parse(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from arbitrary LLM text."""
    text = text.strip()
    # Remove markdown fences
    import re
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {}


# ---------------------------------------------------------------------------
# Pipeline-mode evaluation
# ---------------------------------------------------------------------------

def _run_pipeline_mode(
    question: EvalQuestion,
    model_name: str,
    model_provider: str,
) -> EvalRecord:
    """Run the full 6-node ReasoningPipeline for one (model, question) pair."""
    record = EvalRecord(
        question_id=question.question_id,
        question_text=question.text,
        enzyme=question.enzyme,
        mutation=question.mutation,
        model_name=model_name,
        model_provider=model_provider,
        mode="pipeline",
    )

    try:
        # Import here to avoid loading transformers/torch at module level
        from src.reasoning import ReasoningPipeline

        adapter = _RegistryLLMAdapter(model_name, temperature=0.0)
        pipeline = ReasoningPipeline(llm_provider=adapter)

        t0 = time.perf_counter()
        trace = pipeline.execute(question.evidence)
        elapsed = time.perf_counter() - t0

        # Build a clean output from the pipeline synthesis
        synthesis = trace.final_explanation or ""
        if not synthesis and trace.nodes:
            # Fall back: concatenate all node outputs
            node_texts = []
            for n in trace.nodes:
                for v in n.output.values():
                    if isinstance(v, str) and len(v) > 20:
                        node_texts.append(v)
            synthesis = " ".join(node_texts)

        # Serialise the trace for the report (exclude large embeddings)
        trace_dict = {
            "enzyme": trace.enzyme,
            "completed_nodes": trace.completed_nodes,
            "total_nodes": trace.total_nodes,
            "supported_claims": trace.supported_claims,
            "total_claims": trace.total_claims,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_name": n.node_name,
                    "output": n.output,
                    "confidence": n.confidence,
                    "reasoning_chain": n.reasoning_chain,
                }
                for n in trace.nodes
            ],
        }

        record.model_output   = synthesis
        record.pipeline_trace = trace_dict
        record.latency_seconds = elapsed + adapter._total_latency
        record.token_count    = adapter._total_tokens
        record.success        = True

    except Exception as exc:
        logger.warning(
            "[pipeline] %s / %s failed: %s",
            model_name, question.question_id, exc,
        )
        record.error   = str(exc)
        record.success = False

    return record


# ---------------------------------------------------------------------------
# Direct-mode evaluation
# ---------------------------------------------------------------------------

_DIRECT_SYSTEM_PROMPT = """\
You are a expert biochemist and neuroscience drug-discovery researcher.
Answer the question precisely using ONLY the supplied evidence.
Do not invent facts, kinetic values, drug names, or variant codes \
that are not present in the evidence.
Structure your answer with clear mechanistic steps.
"""

_DIRECT_USER_TEMPLATE = """\
EVIDENCE:
{evidence}

QUESTION:
{question}

Provide a detailed, mechanistically accurate answer grounded in the above evidence.
"""


def _run_direct_mode(
    question: EvalQuestion,
    model_name: str,
    model_provider: str,
) -> EvalRecord:
    """Single-shot direct question answer (no multi-step pipeline)."""
    record = EvalRecord(
        question_id=question.question_id,
        question_text=question.text,
        enzyme=question.enzyme,
        mutation=question.mutation,
        model_name=model_name,
        model_provider=model_provider,
        mode="direct",
    )

    messages = [
        {"role": "system", "content": _DIRECT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _DIRECT_USER_TEMPLATE.format(
                evidence=question.evidence_summary(),
                question=question.text,
            ),
        },
    ]

    t0 = time.perf_counter()
    try:
        response: ChatResponse = chat(
            model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=2048,
        )
        elapsed = time.perf_counter() - t0

        record.model_output    = response.content
        record.latency_seconds = elapsed
        record.token_count     = response.token_count
        record.success         = response.success
        if not response.success:
            record.error = response.error

    except Exception as exc:
        logger.warning(
            "[direct] %s / %s failed: %s",
            model_name, question.question_id, exc,
        )
        record.error           = str(exc)
        record.latency_seconds = time.perf_counter() - t0
        record.success         = False

    return record


# ---------------------------------------------------------------------------
# Public evaluator
# ---------------------------------------------------------------------------

def run_evaluation(
    models: Optional[List[str]] = None,
    question_ids: Optional[List[str]] = None,
    mode: str = "pipeline",
    verbose: bool = True,
) -> List[EvalRecord]:
    """
    Run the full evaluation matrix: all (model × question) combinations.

    Args:
        models:       List of model registry keys to evaluate.
                      Defaults to ALL_MODEL_NAMES.
        question_ids: List of question IDs (e.g. ['Q1', 'Q3']).
                      Defaults to all 5 questions.
        mode:         "pipeline" (full TRACE-Reason pipeline) or
                      "direct" (single-shot Q&A).
        verbose:      Print progress to stdout.

    Returns:
        List of EvalRecord, one per (model, question) pair.
    """
    if models is None:
        models = ALL_MODEL_NAMES
    questions = get_questions(question_ids)

    records: List[EvalRecord] = []
    total = len(models) * len(questions)
    done  = 0

    for model_name in models:
        from eval.model_registry import get_provider
        provider = get_provider(model_name)

        for question in questions:
            done += 1
            if verbose:
                print(
                    f"  [{done:>3}/{total}] {model_name:40s} × {question.question_id}",
                    flush=True,
                )

            if mode == "pipeline":
                record = _run_pipeline_mode(question, model_name, provider)
            else:
                record = _run_direct_mode(question, model_name, provider)

            if verbose:
                status = "✓" if record.success else "✗"
                print(
                    f"         {status}  latency={record.latency_seconds:.1f}s  "
                    f"tokens={record.token_count}",
                    flush=True,
                )
            records.append(record)

    return records
