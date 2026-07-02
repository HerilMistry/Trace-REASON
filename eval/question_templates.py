"""
question_templates.py
=====================
Generates EvalQuestion objects from the extended enzyme database using
3 templated question types per enzyme:

  Q-ActiveSite:  Active-site architecture + inhibitor mechanism
  Q-MoA:         Mechanism-of-action comparison between drugs
  Q-DrugAbility: Druggability assessment across target classes

This scales the benchmark from 3 hand-coded questions (Q6-Q8) to
up to 213 auto-generated questions (71 enzymes × 3 templates).

Usage:
    from eval.question_templates import generate_extended_bank, BENCHMARK_SUITES
    questions = generate_extended_bank()               # all enzymes, all 3 types
    questions = generate_extended_bank(category="cancer")  # cancer only
    questions = generate_extended_bank(suite="TRACE-Neuro-29")
"""

from __future__ import annotations

import sys
import os
import logging
from typing import Dict, List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from eval.db_loader import load_all_enzymes, load_by_category
from eval.questions import EvalQuestion

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Benchmark suites
# ---------------------------------------------------------------------------

BENCHMARK_SUITES: Dict[str, Dict] = {
    "TRACE-Neuro-29":      {"category": "neurological",           "description": "29 neurological enzyme targets"},
    "TRACE-Onco-19":       {"category": "cancer",                 "description": "19 cancer enzyme targets"},
    "TRACE-Cardio-8":      {"category": "cardiovascular",         "description": "8 cardiovascular enzyme targets"},
    "TRACE-Metabolic-8":   {"category": "metabolic",              "description": "8 metabolic/diabetes enzyme targets"},
    "TRACE-Immune-11":     {"category": "inflammatory",           "description": "11 inflammatory/autoimmune enzyme targets"},
    "TRACE-Infectious-8":  {"category": "infectious",             "description": "8 infectious disease enzyme targets"},
    "TRACE-Rare-9":        {"category": "rare",                   "description": "9 rare/genetic disease enzyme targets"},
    "TRACE-Full-71":       {"category": None,                     "description": "All 71 enzymes across 7 disease categories"},
}


# ---------------------------------------------------------------------------
# Question template builders
# ---------------------------------------------------------------------------

def _build_active_site_question(enzyme: Dict, idx: int) -> Optional[EvalQuestion]:
    """Q-ActiveSite: Active-site architecture + drug mechanism."""
    active_site = enzyme.get("active_site_residues", "")
    if not active_site:
        return None

    ev = enzyme["evidence"]
    inhibitors = ev.inhibitors[:2]
    if not inhibitors:
        return None

    drug_str = " and ".join(inhibitors)

    text = (
        f"Describe the active-site architecture of {enzyme['enzyme_name']} "
        f"({enzyme['gene_symbol']}, EC {ev.metadata.ec_number}) and explain how "
        f"its catalytic residues ({active_site[:120]}) enable substrate processing. "
        f"How do inhibitors like {drug_str} exploit the active-site geometry to "
        f"block enzymatic activity? Reference the supplied evidence to support "
        f"your mechanistic explanation."
    )

    return EvalQuestion(
        question_id=f"QAS-{idx:03d}",
        text=text,
        enzyme=enzyme["gene_symbol"],
        mutation=None,
        evidence=ev,
    )


def _build_moa_question(enzyme: Dict, idx: int) -> Optional[EvalQuestion]:
    """Q-MoA: Mechanism-of-action comparison between drugs."""
    ev = enzyme["evidence"]
    inhibitors = ev.inhibitors
    if len(inhibitors) < 2:
        return None

    drug_1, drug_2 = inhibitors[0], inhibitors[1]

    text = (
        f"Compare the mechanism-of-action of {drug_1} and {drug_2} as inhibitors "
        f"of {enzyme['enzyme_name']} ({enzyme['gene_symbol']}). "
        f"Using the supplied evidence — including active-site residues, substrates, "
        f"products, and known variants — explain: "
        f"(1) how each drug interacts with the enzyme's binding site; "
        f"(2) whether their inhibition is competitive, non-competitive, or covalent; "
        f"(3) which drug is likely more selective and why, given the enzyme's "
        f"{enzyme['enzyme_class']} classification and the disease context "
        f"({ev.disease.indication})."
    )

    return EvalQuestion(
        question_id=f"QMoA-{idx:03d}",
        text=text,
        enzyme=enzyme["gene_symbol"],
        mutation=None,
        evidence=ev,
    )


def _build_drugability_question(enzyme: Dict, idx: int) -> Optional[EvalQuestion]:
    """Q-DrugAbility: Druggability assessment."""
    ev = enzyme["evidence"]
    druggability = enzyme.get("druggability", "")

    text = (
        f"Assess the druggability of {enzyme['enzyme_name']} ({enzyme['gene_symbol']}) "
        f"as a therapeutic target for {ev.disease.indication}. "
        f"Given its classification as a {enzyme['enzyme_class']}, "
        f"its known inhibitors ({', '.join(ev.inhibitors[:3]) if ev.inhibitors else 'none listed'}), "
        f"and the pathogenic variant landscape "
        f"({', '.join(ev.pathogenic_variants[:2]) if ev.pathogenic_variants else 'no common variants'}), "
        f"evaluate: "
        f"(1) what active-site features make this enzyme druggable or undruggable; "
        f"(2) whether existing clinical compounds have succeeded or failed and why; "
        f"(3) what the most promising therapeutic strategy is based on the supplied "
        f"evidence package."
    )

    return EvalQuestion(
        question_id=f"QDA-{idx:03d}",
        text=text,
        enzyme=enzyme["gene_symbol"],
        mutation=None,
        evidence=ev,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_extended_bank(
    category: Optional[str] = None,
    suite: Optional[str] = None,
    question_types: Optional[List[str]] = None,
) -> List[EvalQuestion]:
    """
    Generate the full extended question bank from the database.

    Args:
        category:       Filter by disease category (e.g. 'cancer', 'neurological')
        suite:          Use a named benchmark suite (e.g. 'TRACE-Neuro-29')
        question_types: List of types to generate: ['active_site', 'moa', 'drugability']
                        Defaults to all 3.

    Returns:
        List of EvalQuestion objects.
    """
    # Resolve suite → category
    if suite:
        if suite not in BENCHMARK_SUITES:
            raise ValueError(f"Unknown suite '{suite}'. Available: {list(BENCHMARK_SUITES.keys())}")
        suite_info = BENCHMARK_SUITES[suite]
        category = suite_info["category"]
        logger.info("Using suite %s: %s", suite, suite_info["description"])

    # Load enzymes
    if category:
        enzymes = load_by_category(category)
    else:
        enzymes = load_all_enzymes()

    if not enzymes:
        logger.warning("No enzymes loaded for category=%s, suite=%s", category, suite)
        return []

    # Determine which question types to generate
    types = question_types or ["active_site", "moa", "drugability"]
    builders = {
        "active_site": _build_active_site_question,
        "moa":         _build_moa_question,
        "drugability": _build_drugability_question,
    }

    questions: List[EvalQuestion] = []
    idx = 1

    for enzyme in enzymes:
        for qtype in types:
            builder = builders.get(qtype)
            if not builder:
                continue
            q = builder(enzyme, idx)
            if q:
                questions.append(q)
                idx += 1

    logger.info("Generated %d questions from %d enzymes (types: %s)",
                len(questions), len(enzymes), types)
    return questions


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TRACE-Reason Question Template Engine")
    parser.add_argument("--suite", default=None, help="Named benchmark suite")
    parser.add_argument("--category", default=None, help="Disease category filter")
    parser.add_argument("--types", default="active_site,moa,drugability", help="Comma-separated question types")
    args = parser.parse_args()

    types = [t.strip() for t in args.types.split(",")]
    questions = generate_extended_bank(
        category=args.category,
        suite=args.suite,
        question_types=types,
    )

    print(f"\n📋 Generated {len(questions)} questions\n")

    # Show available suites
    print("Available benchmark suites:")
    for name, info in BENCHMARK_SUITES.items():
        cat = info['category'] or 'all'
        filtered = generate_extended_bank(suite=name)
        print(f"  {name:25s}  {info['description']:45s}  → {len(filtered)} questions")
    print()

    # Show first few questions
    print("Sample questions (first 6):")
    for q in questions[:6]:
        print(f"  [{q.question_id}] {q.enzyme:10s} — {q.text[:90]}...")
    print()
