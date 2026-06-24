#!/usr/bin/env python3
"""
run_eval.py
===========
Single entry-point CLI for the TRACE-Reason multi-model evaluation harness.

Usage
-----
  # Full evaluation of LRRK2 G2019S across all free-tier models:
  python run_eval.py --enzyme LRRK2 --mutation G2019S

  # Quick test with specific models and questions:
  python run_eval.py --enzyme BACE1 --models groq/gemma2-9b-it --questions Q3

  # Direct-mode (no pipeline, just Q&A):
  python run_eval.py --enzyme GSK3B --mode direct

  # Dry-run (validates setup, no API calls):
  python run_eval.py --dry-run

  # Show only specific models:
  python run_eval.py --models "groq/llama-3.3-70b-versatile,gemini/gemini-1.5-flash"

Environment Variables Required
-------------------------------
  GROQ_API_KEY       – Groq cloud API key
  GOOGLE_API_KEY     – Google AI Studio / Gemini API key
  MISTRAL_API_KEY    – Mistral La Plateforme API key
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Ensure the project root is on sys.path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "google.auth", "google.api_core"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Dry-run validation
# ---------------------------------------------------------------------------

def _dry_run() -> None:
    """Validate imports, API keys, and evidence fixtures without calling any APIs."""
    print("\n🔍  TRACE-Reason Eval Harness — DRY RUN\n" + "─" * 50)

    # 1. Check imports
    print("\n[1/4] Checking imports…")
    errors = []
    try:
        from eval.model_registry import MODELS, check_api_keys
        print(f"      ✓ model_registry  ({len(MODELS)} models registered)")
    except Exception as e:
        errors.append(f"model_registry: {e}")

    try:
        from eval.questions import QUESTION_BANK
        print(f"      ✓ questions       ({len(QUESTION_BANK)} questions)")
    except Exception as e:
        errors.append(f"questions: {e}")

    try:
        from eval.metrics import extract_claims, compute_hallucination_rate
        print("      ✓ metrics")
    except Exception as e:
        errors.append(f"metrics: {e}")

    try:
        from eval.judge import score
        print("      ✓ judge")
    except Exception as e:
        errors.append(f"judge: {e}")

    try:
        from eval.evaluator import run_evaluation
        print("      ✓ evaluator")
    except Exception as e:
        errors.append(f"evaluator: {e}")

    try:
        from eval.leaderboard import build_leaderboard, print_leaderboard
        print("      ✓ leaderboard")
    except Exception as e:
        errors.append(f"leaderboard: {e}")

    if errors:
        print("\n  ✗ Import errors:")
        for err in errors:
            print(f"    - {err}")
        sys.exit(1)

    # 2. Check API keys
    print("\n[2/4] Checking API keys…")
    from eval.model_registry import check_api_keys
    keys = check_api_keys()
    for k, present in keys.items():
        status = "✓" if present else "✗ MISSING"
        print(f"      {status}  {k}")

    # 3. Validate evidence fixtures
    print("\n[3/4] Validating evidence fixtures…")
    from eval.questions import QUESTION_BANK
    for q in QUESTION_BANK:
        summary = q.evidence_summary()
        print(f"      ✓ {q.question_id}: {q.enzyme} — {len(summary.splitlines())} evidence lines")

    # 4. Test claim extraction on a sample
    print("\n[4/4] Testing claim extraction…")
    from eval.metrics import extract_claims, compute_hallucination_rate
    from eval.questions import QUESTION_BANK
    sample_text = (
        "LRRK2 G2019S is a gain-of-function mutation at position 2019. "
        "It elevates kcat from 3.5 to 9.8 s⁻¹, a 2.8× increase. "
        "This hyperactivation leads to excessive phosphorylation of Rab8A and Rab10. "
        "The mutation is the most common familial Parkinson's cause."
    )
    q = QUESTION_BANK[0]
    try:
        ev_dict = q.evidence.dict()
    except AttributeError:
        ev_dict = q.evidence.model_dump()
    claims = extract_claims(sample_text)
    report = compute_hallucination_rate(sample_text, ev_dict)
    print(f"      ✓ extracted {len(claims)} claims, hallucination_rate={report.hallucination_rate:.3f}")

    print("\n✅  Dry run complete — all checks passed.\n")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TRACE-Reason Multi-Model Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--enzyme", default="LRRK2",
        help="Primary enzyme for the evaluation context (default: LRRK2)",
    )
    parser.add_argument(
        "--mutation", default="G2019S",
        help="Mutation of interest (default: G2019S)",
    )
    parser.add_argument(
        "--questions", default="all",
        help="Comma-separated question IDs to run (e.g. Q1,Q3) or 'all' (default: all)",
    )
    parser.add_argument(
        "--models", default="all",
        help="Comma-separated model registry keys or 'all' (default: all)",
    )
    parser.add_argument(
        "--mode", choices=["pipeline", "direct"], default="pipeline",
        help="Evaluation mode: 'pipeline' (full TRACE-Reason) or 'direct' (single-shot Q&A)",
    )
    parser.add_argument(
        "--output-dir", default="outputs/eval",
        help="Directory for reports, heatmap, and JSON (default: outputs/eval)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate setup without calling any APIs",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--skip-judge", action="store_true",
        help="Skip LLM judge calls (only compute hallucination metrics)",
    )
    parser.add_argument(
        "--judge-retries", type=int, default=3,
        help="Max number of judge candidates to try per output (default: 3)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()
    _setup_logging(args.verbose)

    # ── Dry run ──────────────────────────────────────────────────────────
    if args.dry_run:
        _dry_run()
        return

    # ── Header ───────────────────────────────────────────────────────────
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]🔬 TRACE-Reason Multi-Model Evaluation Harness[/bold cyan]\n"
            f"Enzyme: [yellow]{args.enzyme}[/yellow]   "
            f"Mutation: [yellow]{args.mutation}[/yellow]   "
            f"Mode: [yellow]{args.mode}[/yellow]",
            border_style="cyan",
        ))
    except ImportError:
        print("\n🔬 TRACE-Reason Multi-Model Evaluation Harness")
        print(f"   Enzyme: {args.enzyme}  |  Mutation: {args.mutation}  |  Mode: {args.mode}\n")

    # ── Resolve models ────────────────────────────────────────────────────
    from eval.model_registry import ALL_MODEL_NAMES, check_api_keys

    if args.models == "all":
        models = ALL_MODEL_NAMES
    else:
        models = [m.strip() for m in args.models.split(",") if m.strip()]

    # Warn about missing API keys
    key_status = check_api_keys()
    missing = [k for k, v in key_status.items() if not v]
    if missing:
        print(f"\n⚠️  Missing API keys: {', '.join(missing)}")
        print("   Affected models will be skipped automatically.\n")

    # ── Resolve questions ─────────────────────────────────────────────────
    if args.questions == "all":
        question_ids = None
    else:
        question_ids = [q.strip() for q in args.questions.split(",") if q.strip()]

    # ── Output directory ──────────────────────────────────────────────────
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path     = str(output_dir / "eval_report.json")
    markdown_path = str(output_dir / "eval_summary.md")
    heatmap_path  = str(output_dir / "eval_heatmap.png")

    print(f"\n📂 Output directory: {output_dir}")
    print(f"   Models: {len(models)}  |  Questions: {'all' if question_ids is None else len(question_ids)}\n")

    # ── Step 1: Run backbone evaluations ──────────────────────────────────
    print("=" * 60)
    print("STEP 1 / 3 — Running backbone models")
    print("=" * 60)

    t_start = time.perf_counter()

    from eval.evaluator import run_evaluation
    eval_records = run_evaluation(
        models=models,
        question_ids=question_ids,
        mode=args.mode,
        verbose=True,
    )

    t_eval = time.perf_counter() - t_start
    n_success = sum(1 for r in eval_records if r.success)
    print(f"\n  ✓ Done — {n_success}/{len(eval_records)} calls succeeded in {t_eval:.1f}s\n")

    # ── Step 2: Judge scoring ─────────────────────────────────────────────
    print("=" * 60)
    print("STEP 2 / 3 — LLM judge scoring")
    print("=" * 60)

    from eval.judge import batch_score, JudgeResult

    if args.skip_judge:
        print("  (skipped — --skip-judge flag set)\n")
        judge_results = [
            JudgeResult(
                question_id=r.question_id,
                backbone_model=r.model_name,
                judge_model="SKIPPED",
                faithfulness=3,
                correctness=3,
                completeness=3,
                reasoning="Judge scoring was skipped.",
            )
            for r in eval_records
        ]
    else:
        judge_results = batch_score(
            eval_records,
            max_retries=args.judge_retries,
            temperature=0.0,
        )
        n_judge_ok = sum(1 for j in judge_results if not j.judge_error)
        print(f"\n  ✓ Done — {n_judge_ok}/{len(judge_results)} judge calls succeeded\n")

    # ── Step 3: Hallucination metrics ─────────────────────────────────────
    print("=" * 60)
    print("STEP 3 / 3 — Computing hallucination metrics")
    print("=" * 60)

    from eval.metrics import compute_hallucination_rate, HallucinationReport
    from eval.questions import QUESTION_BY_ID

    hallucination_reports: List[HallucinationReport] = []
    for rec in eval_records:
        q = QUESTION_BY_ID.get(rec.question_id)
        if q and rec.model_output:
            try:
                ev_dict = q.evidence.dict()
            except AttributeError:
                ev_dict = q.evidence.model_dump()
            report = compute_hallucination_rate(rec.model_output, ev_dict)
        else:
            report = HallucinationReport(
                tags=[], total_claims=0, supported_claims=0,
                unsupported_claims=0, hallucination_rate=0.0,
            )
        hallucination_reports.append(report)
        if rec.success:
            print(
                f"  {rec.model_name:40s} × {rec.question_id}"
                f"  claims={report.total_claims:>3}  "
                f"halluc={report.hallucination_rate:.3f}"
            )

    print()

    # ── Build leaderboard ─────────────────────────────────────────────────
    from eval.leaderboard import (
        build_leaderboard,
        generate_heatmap,
        save_json_report,
        save_markdown_summary,
        print_leaderboard,
    )

    meta = {
        "enzyme": args.enzyme,
        "mutation": args.mutation,
        "mode": args.mode,
        "n_questions": len(question_ids) if question_ids else 5,
        "n_models": len(models),
        "evaluation_time_seconds": round(time.perf_counter() - t_start, 2),
    }

    rows, aggregates = build_leaderboard(eval_records, judge_results, hallucination_reports)

    # ── Print to console ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🏆  LEADERBOARD")
    print("=" * 60 + "\n")
    print_leaderboard(aggregates)

    # ── Save outputs ──────────────────────────────────────────────────────
    print(f"\n\n💾  Saving outputs to {output_dir} …")

    save_json_report(rows, aggregates, eval_records, judge_results, json_path, meta)
    print(f"   ✓ JSON report  → {json_path}")

    heatmap_ok = generate_heatmap(aggregates, heatmap_path)
    if heatmap_ok:
        print(f"   ✓ Heatmap PNG  → {heatmap_path}")

    save_markdown_summary(
        rows, aggregates,
        heatmap_path=heatmap_path if heatmap_ok else None,
        output_path=markdown_path,
        meta=meta,
    )
    print(f"   ✓ Markdown     → {markdown_path}")

    # ── Final summary ─────────────────────────────────────────────────────
    total_time = time.perf_counter() - t_start
    best = aggregates[0] if aggregates else None
    print("\n" + "─" * 60)
    if best:
        print(f"🥇  Best model: {best.model_name}")
        print(f"    Composite score : {best.avg_composite_score:.4f}")
        print(f"    Faithfulness    : {best.avg_faithfulness:.2f}/5")
        print(f"    Correctness     : {best.avg_correctness:.2f}/5")
        print(f"    Completeness    : {best.avg_completeness:.2f}/5")
        print(f"    Hallucination ↓ : {best.avg_hallucination_rate:.3f}")
        print(f"    Avg latency     : {best.avg_latency:.1f}s")
    print(f"\n⏱️   Total wall time: {total_time:.1f}s")
    print("─" * 60 + "\n")


if __name__ == "__main__":
    main()
