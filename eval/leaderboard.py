"""
leaderboard.py
==============
Aggregation, composite scoring, and reporting for the TRACE-Reason
multi-model evaluation harness.

Composite score formula:
    composite = (faithfulness + correctness + completeness) / 3
                * (1 - hallucination_rate)

Outputs:
  - Ranked leaderboard table (console + markdown)
  - Per-question breakdown table
  - Heatmap PNG (model × metric)
  - JSON report (full data)
  - Markdown summary

All output is written to the specified output directory.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Aggregated row — one row per (model × question)
# ---------------------------------------------------------------------------

@dataclass
class LeaderboardRow:
    model_name: str
    provider: str
    question_id: str
    enzyme: str
    mode: str

    # From judge
    faithfulness: float = 0.0
    correctness: float = 0.0
    completeness: float = 0.0
    judge_model: str = ""
    judge_error: Optional[str] = None
    unsupported_claims: List[str] = field(default_factory=list)

    # From metrics
    hallucination_rate: float = 0.0
    total_claims: int = 0

    # From evaluator
    latency_seconds: float = 0.0
    token_count: int = 0
    backbone_success: bool = False
    backbone_error: Optional[str] = None

    # Computed
    composite_score: float = 0.0

    def compute_composite(self) -> float:
        """(F+C+C)/3 * (1 - H_rate), clamped to [0, 1]."""
        mean_rubric = (self.faithfulness + self.correctness + self.completeness) / 3.0
        # Normalise to [0, 1]: rubric is in [1, 5], so subtract 1 and divide by 4
        mean_norm = (mean_rubric - 1.0) / 4.0
        self.composite_score = round(max(0.0, mean_norm * (1.0 - self.hallucination_rate)), 4)
        return self.composite_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "question_id": self.question_id,
            "enzyme": self.enzyme,
            "mode": self.mode,
            "faithfulness": self.faithfulness,
            "correctness": self.correctness,
            "completeness": self.completeness,
            "hallucination_rate": self.hallucination_rate,
            "composite_score": self.composite_score,
            "latency_seconds": self.latency_seconds,
            "token_count": self.token_count,
            "judge_model": self.judge_model,
            "backbone_success": self.backbone_success,
            "backbone_error": self.backbone_error,
            "judge_error": self.judge_error,
            "unsupported_claims": self.unsupported_claims,
            "total_claims": self.total_claims,
        }


# ---------------------------------------------------------------------------
# Model aggregate (average across all questions)
# ---------------------------------------------------------------------------

@dataclass
class ModelAggregate:
    model_name: str
    provider: str
    mode: str
    n_questions: int
    n_successful: int

    avg_faithfulness: float = 0.0
    avg_correctness: float = 0.0
    avg_completeness: float = 0.0
    avg_hallucination_rate: float = 0.0
    avg_composite_score: float = 0.0
    avg_latency: float = 0.0
    avg_tokens: float = 0.0

    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "model_name": self.model_name,
            "provider": self.provider,
            "mode": self.mode,
            "n_questions": self.n_questions,
            "n_successful": self.n_successful,
            "avg_faithfulness": round(self.avg_faithfulness, 3),
            "avg_correctness": round(self.avg_correctness, 3),
            "avg_completeness": round(self.avg_completeness, 3),
            "avg_hallucination_rate": round(self.avg_hallucination_rate, 3),
            "avg_composite_score": round(self.avg_composite_score, 4),
            "avg_latency_s": round(self.avg_latency, 2),
            "avg_tokens": round(self.avg_tokens, 0),
        }


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_leaderboard(
    eval_records: List[Any],    # List[EvalRecord]
    judge_results: List[Any],   # List[JudgeResult]
    hallucination_reports: List[Any],  # List[HallucinationReport]
) -> Tuple[List[LeaderboardRow], List[ModelAggregate]]:
    """
    Combine evaluator outputs, judge scores, and hallucination reports
    into LeaderboardRows, then aggregate per model.

    Args:
        eval_records:          One per (model × question)
        judge_results:         Parallel list of JudgeResults
        hallucination_reports: Parallel list of HallucinationReports

    Returns:
        (rows, aggregates) — rows sorted by composite score descending;
        aggregates sorted by avg_composite_score descending with ranks assigned.
    """
    from eval.model_registry import get_provider

    rows: List[LeaderboardRow] = []

    for rec, jres, hrep in zip(eval_records, judge_results, hallucination_reports):
        row = LeaderboardRow(
            model_name=rec.model_name,
            provider=rec.model_provider,
            question_id=rec.question_id,
            enzyme=rec.enzyme,
            mode=rec.mode,
            # Judge scores
            faithfulness=float(jres.faithfulness),
            correctness=float(jres.correctness),
            completeness=float(jres.completeness),
            judge_model=jres.judge_model,
            judge_error=jres.judge_error,
            unsupported_claims=jres.unsupported_claims,
            # Hallucination
            hallucination_rate=hrep.hallucination_rate,
            total_claims=hrep.total_claims,
            # Eval record
            latency_seconds=rec.latency_seconds,
            token_count=rec.token_count,
            backbone_success=rec.success,
            backbone_error=rec.error,
        )
        row.compute_composite()
        rows.append(row)

    rows.sort(key=lambda r: r.composite_score, reverse=True)

    # Aggregate per model
    from collections import defaultdict
    model_rows: Dict[str, List[LeaderboardRow]] = defaultdict(list)
    for row in rows:
        model_rows[row.model_name].append(row)

    aggregates: List[ModelAggregate] = []
    for model_name, mrs in model_rows.items():
        successful = [r for r in mrs if r.backbone_success]
        n = len(mrs)
        ns = len(successful)

        def _mean(attr: str, src=successful) -> float:
            return float(np.mean([getattr(r, attr) for r in src])) if src else 0.0

        agg = ModelAggregate(
            model_name=model_name,
            provider=mrs[0].provider,
            mode=mrs[0].mode,
            n_questions=n,
            n_successful=ns,
            avg_faithfulness=_mean("faithfulness"),
            avg_correctness=_mean("correctness"),
            avg_completeness=_mean("completeness"),
            avg_hallucination_rate=_mean("hallucination_rate"),
            avg_composite_score=_mean("composite_score"),
            avg_latency=_mean("latency_seconds", src=mrs),
            avg_tokens=_mean("token_count", src=mrs),
        )
        aggregates.append(agg)

    aggregates.sort(key=lambda a: a.avg_composite_score, reverse=True)
    for rank, agg in enumerate(aggregates, start=1):
        agg.rank = rank

    return rows, aggregates


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------

def _medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")


def render_leaderboard_table(aggregates: List[ModelAggregate]) -> str:
    """Return a formatted markdown/console leaderboard table."""
    try:
        from tabulate import tabulate
        headers = [
            "Rank", "Model", "Provider",
            "Composite↓", "Faith.", "Correct.", "Complete.",
            "Halluc.↓", "Latency(s)", "Tokens",
            "Success",
        ]
        rows = []
        for agg in aggregates:
            rows.append([
                _medal(agg.rank),
                agg.model_name.split("/")[-1],  # short name
                agg.provider,
                f"{agg.avg_composite_score:.4f}",
                f"{agg.avg_faithfulness:.2f}",
                f"{agg.avg_correctness:.2f}",
                f"{agg.avg_completeness:.2f}",
                f"{agg.avg_hallucination_rate:.3f}",
                f"{agg.avg_latency:.1f}",
                f"{agg.avg_tokens:.0f}",
                f"{agg.n_successful}/{agg.n_questions}",
            ])
        return tabulate(rows, headers=headers, tablefmt="github")
    except ImportError:
        # Plain fallback
        lines = ["| Rank | Model | Composite | Faithfulness | Correctness | Completeness | Halluc. |"]
        lines.append("|---|---|---|---|---|---|---|")
        for agg in aggregates:
            lines.append(
                f"| {_medal(agg.rank)} | {agg.model_name} | "
                f"{agg.avg_composite_score:.4f} | {agg.avg_faithfulness:.2f} | "
                f"{agg.avg_correctness:.2f} | {agg.avg_completeness:.2f} | "
                f"{agg.avg_hallucination_rate:.3f} |"
            )
        return "\n".join(lines)


def render_per_question_table(rows: List[LeaderboardRow]) -> str:
    """Return a per-question breakdown as a markdown table."""
    try:
        from tabulate import tabulate
        headers = ["Q", "Model", "Composite", "Faith.", "Correct.", "Complete.", "Halluc.", "Latency(s)"]
        data = []
        for row in sorted(rows, key=lambda r: (r.question_id, -r.composite_score)):
            data.append([
                row.question_id,
                row.model_name.split("/")[-1],
                f"{row.composite_score:.4f}",
                f"{row.faithfulness:.0f}",
                f"{row.correctness:.0f}",
                f"{row.completeness:.0f}",
                f"{row.hallucination_rate:.3f}",
                f"{row.latency_seconds:.1f}",
            ])
        return tabulate(data, headers=headers, tablefmt="github")
    except ImportError:
        return "\n".join(str(r.to_dict()) for r in rows)


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

def generate_heatmap(
    aggregates: List[ModelAggregate],
    output_path: str,
) -> bool:
    """
    Generate a heatmap PNG: models (rows) × metrics (columns).

    Returns True if the file was saved, False if matplotlib is unavailable.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        import seaborn as sns

        metrics = [
            ("avg_faithfulness",     "Faithfulness\n(1-5)"),
            ("avg_correctness",      "Correctness\n(1-5)"),
            ("avg_completeness",     "Completeness\n(1-5)"),
            ("avg_hallucination_rate", "Hallucination\nRate ↓"),
            ("avg_composite_score",  "Composite\nScore"),
            ("avg_latency",          "Latency (s)"),
        ]

        model_names = [a.model_name.split("/")[-1] for a in aggregates]
        data = np.zeros((len(aggregates), len(metrics)))

        for i, agg in enumerate(aggregates):
            for j, (attr, _) in enumerate(metrics):
                data[i, j] = getattr(agg, attr, 0.0)

        # Normalise each column to [0, 1] for colour (inverted for "lower is better" metrics)
        normed = np.zeros_like(data)
        lower_is_better = {"avg_hallucination_rate", "avg_latency"}
        for j, (attr, _) in enumerate(metrics):
            col = data[:, j]
            col_min, col_max = col.min(), col.max()
            span = col_max - col_min if col_max != col_min else 1.0
            if attr in lower_is_better:
                normed[:, j] = (col_max - col) / span  # invert
            else:
                normed[:, j] = (col - col_min) / span

        fig, ax = plt.subplots(
            figsize=(max(10, len(metrics) * 1.8), max(5, len(aggregates) * 0.8 + 2))
        )

        # Background colour map
        cmap = sns.color_palette("YlGnBu", as_cmap=True)
        im = ax.imshow(normed, cmap=cmap, aspect="auto", vmin=0, vmax=1)

        # Annotate cells with actual values
        for i in range(len(aggregates)):
            for j, (attr, _) in enumerate(metrics):
                val = data[i, j]
                if attr == "avg_latency":
                    txt = f"{val:.1f}s"
                elif attr == "avg_hallucination_rate":
                    txt = f"{val:.3f}"
                elif attr in ("avg_faithfulness", "avg_correctness", "avg_completeness"):
                    txt = f"{val:.2f}"
                else:
                    txt = f"{val:.4f}"
                brightness = normed[i, j]
                text_color = "white" if brightness > 0.55 else "black"
                ax.text(j, i, txt, ha="center", va="center", fontsize=9,
                        color=text_color, fontweight="bold")

        ax.set_xticks(range(len(metrics)))
        ax.set_xticklabels([m[1] for m in metrics], fontsize=9)
        ax.set_yticks(range(len(aggregates)))
        ax.set_yticklabels(model_names, fontsize=9)
        ax.set_title(
            "TRACE-Reason Multi-Model Evaluation Heatmap\n"
            "(colour = normalised rank within metric; ↓ = lower is better)",
            fontsize=11, pad=14,
        )

        # Rank labels on left
        for i, agg in enumerate(aggregates):
            ax.text(
                -0.6, i, _medal(agg.rank),
                ha="right", va="center", fontsize=11,
                transform=ax.transData,
            )

        plt.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("Heatmap saved → %s", output_path)
        return True

    except ImportError as exc:
        logger.warning("Heatmap skipped (missing library: %s)", exc)
        return False


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------

def save_json_report(
    rows: List[LeaderboardRow],
    aggregates: List[ModelAggregate],
    eval_records: List[Any],
    judge_results: List[Any],
    output_path: str,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    report = {
        "generated_at": datetime.now().isoformat(),
        "meta": meta or {},
        "leaderboard": [a.to_dict() for a in aggregates],
        "per_question_rows": [r.to_dict() for r in rows],
        "raw_eval_records": [r.to_dict() for r in eval_records],
        "raw_judge_results": [j.to_dict() for j in judge_results],
    }
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info("JSON report saved → %s", output_path)


# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------

def save_markdown_summary(
    rows: List[LeaderboardRow],
    aggregates: List[ModelAggregate],
    heatmap_path: Optional[str],
    output_path: str,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    meta = meta or {}
    lines = [
        "# TRACE-Reason Multi-Model Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Enzyme:** {meta.get('enzyme', 'N/A')}  ",
        f"**Mutation:** {meta.get('mutation', 'N/A')}  ",
        f"**Mode:** {meta.get('mode', 'N/A')}  ",
        f"**Models evaluated:** {len(aggregates)}  ",
        f"**Questions:** {meta.get('n_questions', 'N/A')}",
        "",
        "---",
        "",
        "## 🏆 Overall Leaderboard",
        "",
        "> Composite = (Faithfulness + Correctness + Completeness) / 3 × (1 − Hallucination Rate)",
        "> Scores normalised to [0, 1]. Higher is better. Hallucination Rate: lower is better.",
        "",
        render_leaderboard_table(aggregates),
        "",
        "---",
        "",
        "## 📊 Per-Question Breakdown",
        "",
        render_per_question_table(rows),
        "",
        "---",
        "",
    ]

    if heatmap_path and os.path.exists(heatmap_path):
        lines += [
            "## 🔥 Heatmap: Model × Metric",
            "",
            f"![TRACE-Reason Evaluation Heatmap]({heatmap_path})",
            "",
            "---",
            "",
        ]

    # Key findings
    if aggregates:
        best = aggregates[0]
        worst = aggregates[-1]
        lines += [
            "## 📝 Key Findings",
            "",
            f"- **Best overall model:** {best.model_name} "
            f"(composite = {best.avg_composite_score:.4f})",
            f"- **Lowest hallucination rate:** "
            + (
                lambda a=sorted(aggregates, key=lambda x: x.avg_hallucination_rate):
                f"{a[0].model_name} ({a[0].avg_hallucination_rate:.3f})"
            )(),
            f"- **Fastest model:** "
            + (
                lambda a=sorted(aggregates, key=lambda x: x.avg_latency):
                f"{a[0].model_name} ({a[0].avg_latency:.1f}s avg)"
            )(),
            f"- **Most faithful:** "
            + (
                lambda a=sorted(aggregates, key=lambda x: x.avg_faithfulness, reverse=True):
                f"{a[0].model_name} ({a[0].avg_faithfulness:.2f}/5)"
            )(),
            "",
            "---",
            "",
            "## ℹ️ Methodology",
            "",
            "- **Backbone temperature:** 0.0 (deterministic, reproducible)",
            "- **Judge temperature:** 0.0",
            "- **Judge rotation:** Each model is scored by a judge from a different provider",
            "- **Hallucination rate:** atomic claims extracted via sentence splitting; "
            "unsupported claims = those not grounded in the evidence package",
            "- **Composite formula:** `(F + C₁ + C₂) / 3 × (1 − H)` where F=Faithfulness, "
            "C₁=Correctness, C₂=Completeness, H=Hallucination rate",
            "",
        ]

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Markdown summary saved → %s", output_path)


# ---------------------------------------------------------------------------
# Convenience: print to console
# ---------------------------------------------------------------------------

def print_leaderboard(aggregates: List[ModelAggregate]) -> None:
    """Pretty-print the leaderboard to stdout."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="🔬 TRACE-Reason Model Leaderboard", show_lines=True)

        table.add_column("Rank",        style="bold yellow", justify="center")
        table.add_column("Model",       style="bold cyan")
        table.add_column("Provider",    style="dim")
        table.add_column("Composite ↑", style="bold green", justify="right")
        table.add_column("Faith.",      justify="right")
        table.add_column("Correct.",    justify="right")
        table.add_column("Complete.",   justify="right")
        table.add_column("Halluc. ↓",  style="bold red", justify="right")
        table.add_column("Latency(s)",  justify="right")
        table.add_column("Success",     justify="center")

        for agg in aggregates:
            table.add_row(
                _medal(agg.rank),
                agg.model_name.split("/")[-1],
                agg.provider,
                f"{agg.avg_composite_score:.4f}",
                f"{agg.avg_faithfulness:.2f}",
                f"{agg.avg_correctness:.2f}",
                f"{agg.avg_completeness:.2f}",
                f"{agg.avg_hallucination_rate:.3f}",
                f"{agg.avg_latency:.1f}",
                f"[green]{agg.n_successful}[/][dim]/{agg.n_questions}[/]",
            )
        console.print(table)
    except ImportError:
        # Plain fallback
        print(render_leaderboard_table(aggregates))
