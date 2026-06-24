"""
metrics.py
==========
Claim extraction and hallucination rate computation for TRACE-Reason eval harness.

Pipeline:
  1. extract_claims(text)       → split output into atomic sentences
  2. check_claim(claim, evidence) → tag each as "supported" or "unsupported"
  3. compute_hallucination_rate  → unsupported_count / total_count ∈ [0, 1]

Grounding strategy: keyword/value matching against the evidence package.
A claim is "supported" if it contains at least one verifiable entity or
numeric value from the evidence package.  This is a conservative heuristic
that avoids penalising valid background biological knowledge; it only flags
claims that directly contradict or fabricate evidence-level specifics.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ClaimTag:
    sentence: str
    supported: bool
    matched_evidence: List[str] = field(default_factory=list)  # which evidence keys matched


@dataclass
class HallucinationReport:
    tags: List[ClaimTag]
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    hallucination_rate: float  # unsupported / total, ∈ [0, 1]

    def summary(self) -> str:
        lines = [
            f"Total claims   : {self.total_claims}",
            f"Supported      : {self.supported_claims}",
            f"Unsupported    : {self.unsupported_claims}",
            f"Hallucination  : {self.hallucination_rate:.3f}",
            "",
            "Unsupported claims:",
        ]
        for tag in self.tags:
            if not tag.supported:
                lines.append(f"  ✗ {tag.sentence[:120]}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

# Sentence boundary patterns.  We use a greedy split on common terminators
# while trying to preserve abbreviations (e.g. "GSK-3β").
_SENTENCE_END = re.compile(
    r"(?<!\w\.\w.)"           # not inside abbreviations like "e.g."
    r"(?<![A-Z][a-z]\."       # not after title abbreviations "Dr."
    r")"
    r"(?<!\d\.\d)"            # not inside decimal numbers "3.5"
    r"([.!?])\s+(?=[A-Z0-9])",  # sentence end + whitespace + capital/digit
    re.MULTILINE,
)

_BULLET_PREFIX = re.compile(r"^\s*[-•*\d]+[.)]\s*")
_HEADING_LINE  = re.compile(r"^#+\s|^\*\*[^*]+\*\*$|^[A-Z ]{4,}:$")


def extract_claims(text: str) -> List[str]:
    """
    Split *text* into a list of atomic factual sentences.

    Steps:
      1. Strip markdown headings and bullet prefixes.
      2. Split on sentence boundaries.
      3. Filter out very short fragments (< 6 words) and pure-number strings.

    Returns:
        List of sentence strings (stripped, non-empty).
    """
    if not text or not text.strip():
        return []

    # Normalise newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove JSON fences / code blocks (we evaluate prose reasoning)
    text = re.sub(r"```[\s\S]*?```", " ", text)

    # Flatten bullet points into plain sentences
    lines = []
    for line in text.split("\n"):
        if _HEADING_LINE.match(line.strip()):
            continue
        line = _BULLET_PREFIX.sub("", line)
        line = line.strip()
        if line:
            lines.append(line)
    flat = " ".join(lines)

    # Split on sentence boundaries
    parts = _SENTENCE_END.split(flat)
    sentences: List[str] = []
    i = 0
    while i < len(parts):
        chunk = parts[i].strip()
        # The regex captures the delimiter in group 1; skip it
        if chunk and not re.fullmatch(r"[.!?]", chunk):
            sentences.append(chunk)
        i += 1

    # Also split on remaining newline-separated clauses
    final: List[str] = []
    for s in sentences:
        sub = [p.strip() for p in s.split("\n") if p.strip()]
        final.extend(sub if sub else [s])

    # Filter noise
    claims = [
        s for s in final
        if len(s.split()) >= 5  # at least 5 words
        and not re.fullmatch(r"[\d\s.,;:]+", s)  # not pure numbers
    ]
    return claims


# ---------------------------------------------------------------------------
# Evidence keyword extraction
# ---------------------------------------------------------------------------

def _build_evidence_keywords(evidence_dict: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Flatten the evidence package into (keyword, source_label) pairs.
    Keywords are lower-cased for matching.
    """
    kws: List[Tuple[str, str]] = []

    def _add(val: Any, label: str) -> None:
        if isinstance(val, str) and val.strip():
            # Add full value and significant tokens (length ≥ 4)
            kws.append((val.lower().strip(), label))
            for tok in re.split(r"[\s,;/()]+", val):
                if len(tok) >= 4:
                    kws.append((tok.lower(), label))
        elif isinstance(val, (int, float)):
            kws.append((str(val), label))
            kws.append((f"{val:.1f}", label))

    # Top-level scalar fields
    for key in ["gene_symbol", "enzyme_name", "uniprot_id", "ec_number"]:
        val = (
            evidence_dict.get("metadata", {}).get(key)
            or evidence_dict.get(key)
        )
        _add(val, f"metadata.{key}")

    # Disease
    for key in ["indication", "target_form", "clinical_stage"]:
        val = evidence_dict.get("disease", {}).get(key, "")
        _add(val, f"disease.{key}")

    # Lists
    for lst_key in ["substrates", "products", "cofactors",
                     "pathogenic_variants", "inhibitors"]:
        for item in evidence_dict.get(lst_key, []):
            _add(item, lst_key)

    # Kinetic evidence
    for kin in evidence_dict.get("kinetic_evidence", []):
        _add(kin.get("parameter", ""), "kinetic.parameter")
        _add(kin.get("value", ""), "kinetic.value")
        _add(kin.get("unit", ""), "kinetic.unit")
        if kin.get("note"):
            _add(kin["note"], "kinetic.note")

    # Mutation evidence
    for mut in evidence_dict.get("mutation_evidence", []):
        pos = mut.get("position", "")
        wt  = mut.get("wildtype_aa", "")
        alt = mut.get("mutant_aa", "")
        if wt and pos and alt:
            kws.append((f"{wt}{pos}{alt}".lower(), "mutation"))
            kws.append((str(pos), "mutation.position"))
        _add(mut.get("mutation_type", ""), "mutation.type")

    return kws


# ---------------------------------------------------------------------------
# Claim support checking
# ---------------------------------------------------------------------------

# Terms that are common biological background — not penalised even if absent
# from the evidence package (these are general scientific vocabulary).
_BACKGROUND_TERMS = {
    "neuron", "protein", "enzyme", "kinase", "phosphorylation", "substrate",
    "disease", "cell", "brain", "pathway", "mechanism", "activity", "function",
    "mutation", "variant", "gene", "amino acid", "atp", "adp", "receptor",
    "signaling", "inhibitor", "drug", "therapeutic", "clinical", "trial",
    "alpha", "beta", "gamma", "domain", "binding", "catalytic", "active site",
    "evidence", "suggest", "indicate", "demonstrate", "study", "research",
    "treatment", "patient", "neurodegeneration", "aggregation", "misfolding",
    "expression", "regulation", "phosphorylate", "cleave", "hydrolyze",
    "complex", "interaction", "downstream", "upstream", "cascade",
    "neurological", "dopamine", "dopaminergic", "synuclein", "amyloid",
    "tau", "neurofibrillary", "lysosome", "mitochondria", "autophagy",
    "ubiquitin", "proteasome", "membrane", "endosome",
}


def check_claim(
    claim: str,
    evidence_keywords: List[Tuple[str, str]],
) -> Tuple[bool, List[str]]:
    """
    Check whether *claim* is grounded in the evidence keywords.

    Returns:
        (is_supported, matched_keys)

    A claim is *supported* if:
      - It contains ≥1 keyword from the evidence package, OR
      - It contains only background biological vocabulary (not penalised).

    A claim is *unsupported* if it introduces specific numeric values,
    gene names, drug names, or variant notations that are NOT in the evidence.
    """
    claim_lower = claim.lower()

    # Check if the claim has specific anchors (numbers, variant codes, drug names)
    has_specific_content = bool(
        re.search(r"\b\d+\.?\d*\s*(µm|nm|ms|mm|pm|s⁻¹|min|mg|kda|ns)", claim_lower)
        or re.search(r"\b[A-Z]\d+[A-Z]\b", claim)   # variant notation e.g. G2019S
        or re.search(r"\b(IC50|Ki|Km|kcat|Vmax)\b", claim, re.IGNORECASE)
    )

    matched: List[str] = []
    for kw, label in evidence_keywords:
        if kw and kw in claim_lower:
            matched.append(label)

    if matched:
        return True, matched

    # If no specific content, it's likely background biology — don't penalise
    words = set(re.findall(r"\b[a-z]{3,}\b", claim_lower))
    background_overlap = words & _BACKGROUND_TERMS
    if not has_specific_content and len(background_overlap) >= 2:
        return True, ["background"]

    # Has specific content but no evidence match → unsupported
    if has_specific_content:
        return False, []

    # Generic sentence, no specific content, low background overlap
    return True, ["generic"]


# ---------------------------------------------------------------------------
# Full hallucination analysis
# ---------------------------------------------------------------------------

def compute_hallucination_rate(
    model_output: str,
    evidence_dict: Dict[str, Any],
) -> HallucinationReport:
    """
    Full hallucination analysis pipeline.

    Args:
        model_output:  Raw text output from the backbone model.
        evidence_dict: Evidence package as a dict (call .dict() or .model_dump()).

    Returns:
        HallucinationReport with per-claim tags and aggregate rate.
    """
    claims = extract_claims(model_output)
    if not claims:
        return HallucinationReport(
            tags=[], total_claims=0, supported_claims=0,
            unsupported_claims=0, hallucination_rate=0.0,
        )

    keywords = _build_evidence_keywords(evidence_dict)
    tags: List[ClaimTag] = []

    for sentence in claims:
        supported, matched = check_claim(sentence, keywords)
        tags.append(ClaimTag(
            sentence=sentence,
            supported=supported,
            matched_evidence=matched,
        ))

    supported_n = sum(1 for t in tags if t.supported)
    unsupported_n = len(tags) - supported_n
    rate = unsupported_n / len(tags) if tags else 0.0

    return HallucinationReport(
        tags=tags,
        total_claims=len(tags),
        supported_claims=supported_n,
        unsupported_claims=unsupported_n,
        hallucination_rate=round(rate, 4),
    )


def extract_unsupported_claims(report: HallucinationReport) -> List[str]:
    """Convenience: return the list of unsupported claim strings."""
    return [t.sentence for t in report.tags if not t.supported]
