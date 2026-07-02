"""
db_loader.py
============
Loads the enzyme_drug_target_database_extended.xlsx and auto-generates
EvidencePackage + EvalQuestion objects for the TRACE-Reason benchmark.

This replaces the hand-coded evidence fixtures in questions.py with a
data-driven approach that scales to 51+ enzymes across 7 disease categories.
"""

from __future__ import annotations

import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Ensure project root is importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.evidence import (
    EvidencePackage,
    MetadataInfo,
    DiseaseInfo,
    MutationEvidence,
    KineticEvidence,
    ReactionEvidence,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "enzyme_drug_target_database_extended.xlsx")

DISEASE_CATEGORY_SHEETS: Dict[str, str] = {
    "neurological":           "Neurological",
    "cancer":                 "Cancer",
    "cardiovascular":         "Cardiovascular",
    "metabolic":              "Metabolic_Diabetes",
    "inflammatory":           "Inflammatory_Autoimmune",
    "infectious":             "Infectious_Disease",
    "rare":                   "Rare_Genetic",
}

# ---------------------------------------------------------------------------
# Variant string parser
# ---------------------------------------------------------------------------

_VARIANT_RE = re.compile(
    r"([A-Z])(\d+)([A-Z])",  # e.g. G2019S, V600E, L858R
)


def _parse_variants(raw: str) -> List[MutationEvidence]:
    """
    Parse the key_pathogenic_variants column into MutationEvidence objects.

    The column contains semicolon-separated entries like:
      'G2019S (pos 2019, G→S, ~1-2% all PD ...); R1441C/G/H (pos 1441); ...'
    We extract the first X###Y pattern from each entry.
    """
    if not raw or str(raw).strip().lower() in ("nan", ""):
        return []

    entries = str(raw).split(";")
    results: List[MutationEvidence] = []
    seen_positions = set()

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        match = _VARIANT_RE.search(entry)
        if match:
            wt, pos_str, mut = match.group(1), match.group(2), match.group(3)
            pos = int(pos_str)
            if pos in seen_positions:
                continue
            seen_positions.add(pos)

            # Determine pathogenicity from context clues
            lower_entry = entry.lower()
            pathogenic = any(kw in lower_entry for kw in [
                "pathogenic", "disruptive", "elevated", "constitutively",
                "gain-of-function", "loss-of-function", "oncogenic",
                "somatic mutation", "drug resistance",
            ])

            # Classify mutation type heuristically
            if pathogenic:
                mut_type = "disruptive"
            elif any(kw in lower_entry for kw in ["benign", "protective", "polymorphism"]):
                mut_type = "benign"
            else:
                mut_type = "moderate"

            results.append(MutationEvidence(
                position=pos,
                wildtype_aa=wt,
                mutant_aa=mut,
                mutation_type=mut_type,
                cosine_similarity=0.80,   # placeholder — no embeddings available
                euclidean_distance=0.50,
                delta_norm=0.45 if mut_type == "moderate" else (0.80 if mut_type == "disruptive" else 0.15),
                pathogenic=pathogenic,
            ))

    return results[:5]  # cap at 5 variants per enzyme to keep evidence manageable


def _split_field(raw: str) -> List[str]:
    """Split a semicolon-delimited field into a cleaned list."""
    if not raw or str(raw).strip().lower() in ("nan", ""):
        return []
    return [s.strip() for s in str(raw).split(";") if s.strip()]


def _safe_str(val, default: str = "") -> str:
    """Convert a possibly-NaN value to a string."""
    s = str(val).strip()
    return default if s.lower() == "nan" else s


# ---------------------------------------------------------------------------
# Row → EvidencePackage
# ---------------------------------------------------------------------------

def _row_to_evidence(row: pd.Series) -> EvidencePackage:
    """Convert one Master-sheet row into an EvidencePackage."""

    gene = _safe_str(row.get("gene_symbol", ""), "UNKNOWN")
    enzyme_name = _safe_str(row.get("enzyme_name", ""), gene)
    uniprot = _safe_str(row.get("uniprot_id", ""), "")
    ec = _safe_str(row.get("ec_number", ""), "")

    # Disease info
    diseases = _safe_str(row.get("all_diseases", ""), "")
    target_form = _safe_str(row.get("target_frequency_and_forms", ""), "")
    druggability = _safe_str(row.get("druggability_assessment", ""), "")

    # Extract clinical stage from drugs column (look for [Phase X] or [Approved])
    drugs_raw = _safe_str(row.get("all_drugs", ""), "")
    stage_match = re.search(r"\[(Approved|Phase\s*\d+)[^\]]*\]", drugs_raw)
    clinical_stage = stage_match.group(0) if stage_match else "Preclinical / Unknown"

    # Substrates, products, cofactors
    substrates = _split_field(row.get("substrates", ""))
    products = _split_field(row.get("products", ""))
    cofactors = _split_field(row.get("cofactors", ""))

    # Drugs as inhibitors
    drug_names = []
    for chunk in _split_field(row.get("all_drugs", "")):
        # Extract just the drug name (before the bracket)
        name_match = re.match(r"^([^[\(]+)", chunk)
        if name_match:
            drug_names.append(name_match.group(1).strip())
    inhibitors = drug_names[:8]  # cap at 8

    # Variant strings for the pathogenic_variants list
    variant_strings = _split_field(row.get("key_pathogenic_variants", ""))[:5]

    # Parsed mutation evidence
    mutation_evidence = _parse_variants(_safe_str(row.get("key_pathogenic_variants", "")))

    # Reaction evidence from enzymatic_reaction column
    reaction_evidence = []
    reaction_raw = _safe_str(row.get("enzymatic_reaction", ""), "")
    if reaction_raw and substrates and products:
        reaction_evidence.append(ReactionEvidence(
            substrate=substrates[0],
            product=products[0],
            cofactor=cofactors[0] if cofactors else None,
            reaction_type=reaction_raw[:150],
        ))

    return EvidencePackage(
        gene_symbol=gene,
        metadata=MetadataInfo(
            gene_symbol=gene,
            enzyme_name=enzyme_name,
            uniprot_id=uniprot,
            ec_number=ec,
        ),
        disease=DiseaseInfo(
            indication=diseases,
            target_form=target_form[:200] if target_form else "",
            clinical_stage=clinical_stage,
        ),
        substrates=substrates,
        products=products,
        cofactors=cofactors,
        pathogenic_variants=variant_strings,
        inhibitors=inhibitors,
        mutation_evidence=mutation_evidence,
        kinetic_evidence=[],       # DB doesn't have kinetic params
        reaction_evidence=reaction_evidence,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_all_enzymes(db_path: Optional[str] = None) -> List[Dict]:
    """
    Load all enzymes from the Master sheet.

    Returns a list of dicts with keys:
        gene_symbol, enzyme_name, disease_category, active_site_residues,
        druggability, evidence (EvidencePackage)
    """
    path = db_path or _DB_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Database not found: {path}")

    df = pd.read_excel(path, sheet_name="Master")
    results = []

    for _, row in df.iterrows():
        gene = _safe_str(row.get("gene_symbol", ""), "")
        if not gene:
            continue

        # Check data completeness
        has_active_site = bool(_safe_str(row.get("active_site_residues", "")))
        has_drugs = bool(_safe_str(row.get("all_drugs", "")))
        has_reaction = bool(_safe_str(row.get("enzymatic_reaction", "")))

        if not (has_active_site and has_drugs and has_reaction):
            continue  # skip enzymes without enough data for meaningful questions

        try:
            evidence = _row_to_evidence(row)
        except Exception as e:
            logger.warning("Failed to build evidence for %s: %s", gene, e)
            continue

        results.append({
            "gene_symbol": gene,
            "enzyme_name": _safe_str(row.get("enzyme_name", "")),
            "disease_category": _safe_str(row.get("all_disease_categories", "")),
            "active_site_residues": _safe_str(row.get("active_site_residues", "")),
            "druggability": _safe_str(row.get("druggability_assessment", "")),
            "enzyme_class": _safe_str(row.get("enzyme_class", "")),
            "evidence": evidence,
        })

    logger.info("Loaded %d enzymes from %s", len(results), path)
    return results


def load_by_category(category: str, db_path: Optional[str] = None) -> List[Dict]:
    """
    Load enzymes filtered to a specific disease category.

    Args:
        category: One of 'neurological', 'cancer', 'cardiovascular',
                  'metabolic', 'inflammatory', 'infectious', 'rare'
    """
    all_enzymes = load_all_enzymes(db_path)
    cat_lower = category.lower()
    return [
        e for e in all_enzymes
        if cat_lower in e["disease_category"].lower()
    ]


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    enzymes = load_all_enzymes()
    print(f"\nLoaded {len(enzymes)} data-rich enzymes from the extended database.\n")
    for e in enzymes[:5]:
        ev = e["evidence"]
        print(f"  {e['gene_symbol']:12s} | {e['enzyme_name'][:35]:35s} | "
              f"{e['disease_category'][:30]:30s} | "
              f"inhibitors={len(ev.inhibitors)} variants={len(ev.mutation_evidence)}")
    print(f"  ... and {len(enzymes) - 5} more.\n")

    # Category breakdown
    from collections import Counter
    cats = Counter()
    for e in enzymes:
        for c in e["disease_category"].split(";"):
            cats[c.strip()] += 1
    print("Category distribution:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")
