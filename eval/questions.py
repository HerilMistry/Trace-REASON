"""
questions.py
============
Fixed evaluation question bank for TRACE-Reason multi-model harness.

Each EvalQuestion bundles:
  - A natural-language question text
  - A pre-built EvidencePackage fixture (hardcoded, no DB/embeddings needed)
  - Metadata (question_id, enzyme, mutation)

Four biological targets are covered: LRRK2, GSK-3β, BACE1, MAO-B.
Eight questions are provided (Q1-Q5 = kinetics/mutation, Q6-Q8 = drug active-site
and drug-ability); the harness runs all of them by default.
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# Ensure the project root is on the path so src.evidence can be imported
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


# ---------------------------------------------------------------------------
# EvalQuestion dataclass
# ---------------------------------------------------------------------------

@dataclass
class EvalQuestion:
    question_id: str
    text: str
    enzyme: str
    mutation: Optional[str]
    evidence: EvidencePackage

    def evidence_summary(self) -> str:
        """Compact text representation of the evidence, used in judge prompts."""
        e = self.evidence
        lines = [
            f"Gene: {e.gene_symbol}",
            f"Enzyme: {e.metadata.enzyme_name}",
            f"UniProt: {e.metadata.uniprot_id}",
            f"EC: {e.metadata.ec_number}",
            f"Disease: {e.disease.indication}",
            f"Target form: {e.disease.target_form}",
            f"Clinical stage: {e.disease.clinical_stage}",
        ]
        if e.substrates:
            lines.append(f"Substrates: {', '.join(e.substrates)}")
        if e.products:
            lines.append(f"Products: {', '.join(e.products)}")
        if e.cofactors:
            lines.append(f"Cofactors: {', '.join(e.cofactors)}")
        if e.pathogenic_variants:
            lines.append(f"Pathogenic variants: {', '.join(e.pathogenic_variants)}")
        if e.inhibitors:
            lines.append(f"Known inhibitors: {', '.join(e.inhibitors)}")
        for k in e.kinetic_evidence:
            note = f" ({k.note})" if k.note else ""
            lines.append(f"Kinetic — {k.parameter}: {k.value} {k.unit}{note}")
        for m in e.mutation_evidence:
            lines.append(
                f"Mutation — {m.wildtype_aa}{m.position}{m.mutant_aa} "
                f"({m.mutation_type}, delta_norm={m.delta_norm:.3f}, "
                f"pathogenic={m.pathogenic})"
            )
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "text": self.text,
            "enzyme": self.enzyme,
            "mutation": self.mutation,
            "evidence_summary": self.evidence_summary(),
        }


# ---------------------------------------------------------------------------
# Evidence fixture builders
# ---------------------------------------------------------------------------

def _build_lrrk2_evidence() -> EvidencePackage:
    """
    LRRK2 — Leucine-rich repeat kinase 2
    Parkinson's Disease | kinase (Ser/Thr) | EC 2.7.11.1
    Key variant: G2019S (gain-of-function in the kinase domain DFG motif)
    """
    return EvidencePackage(
        gene_symbol="LRRK2",
        metadata=MetadataInfo(
            gene_symbol="LRRK2",
            enzyme_name="Leucine-rich repeat serine/threonine-protein kinase 2",
            uniprot_id="Q5S007",
            ec_number="2.7.11.1",
        ),
        disease=DiseaseInfo(
            indication="Parkinson's Disease",
            target_form="Gain-of-function hyperactive kinase (G2019S variant)",
            clinical_stage="Phase 3 — DNL201 (LRRK2 inhibitor, Denali Therapeutics)",
        ),
        substrates=["ATP", "Rab8A (Thr72)", "Rab10 (Thr73)", "Rab35", "RILPL1"],
        products=["ADP", "phospho-Rab8A", "phospho-Rab10", "phospho-Rab35"],
        cofactors=["Mg2+"],
        pathogenic_variants=[
            "G2019S (rs34637584)",
            "R1441C (rs33939927)",
            "R1441G (rs34778348)",
            "Y1699C (rs35007386)",
            "I2020T (rs35870237)",
        ],
        inhibitors=["DNL201", "MLi-2", "PF-475", "GSK2578215A"],
        mutation_evidence=[
            MutationEvidence(
                position=2019,
                wildtype_aa="G",
                mutant_aa="S",
                mutation_type="disruptive",
                cosine_similarity=0.68,
                euclidean_distance=0.91,
                delta_norm=0.82,
                pathogenic=True,
            ),
            MutationEvidence(
                position=1441,
                wildtype_aa="R",
                mutant_aa="C",
                mutation_type="disruptive",
                cosine_similarity=0.71,
                euclidean_distance=0.87,
                delta_norm=0.76,
                pathogenic=True,
            ),
            MutationEvidence(
                position=1699,
                wildtype_aa="Y",
                mutant_aa="C",
                mutation_type="moderate",
                cosine_similarity=0.83,
                euclidean_distance=0.55,
                delta_norm=0.48,
                pathogenic=True,
            ),
        ],
        kinetic_evidence=[
            KineticEvidence(
                parameter="Km(ATP)",
                value=15.0,
                unit="µM",
                note="Michaelis constant for ATP substrate",
            ),
            KineticEvidence(
                parameter="kcat",
                value=3.5,
                unit="s⁻¹",
                note="Catalytic turnover rate (wildtype)",
            ),
            KineticEvidence(
                parameter="kcat_G2019S",
                value=9.8,
                unit="s⁻¹",
                note="~2.8× elevated catalytic rate in G2019S variant",
            ),
            KineticEvidence(
                parameter="Vmax",
                value=0.8,
                unit="nmol·min⁻¹·mg⁻¹",
                note="Maximum velocity under saturating ATP",
            ),
            KineticEvidence(
                parameter="IC50(MLi-2)",
                value=1.4,
                unit="nM",
                note="Tool inhibitor MLi-2 potency against LRRK2",
            ),
        ],
        reaction_evidence=[
            ReactionEvidence(
                substrate="Rab8A",
                product="phospho-Rab8A (Thr72)",
                cofactor="Mg2+-ATP",
                reaction_type="Ser/Thr phosphorylation",
            ),
            ReactionEvidence(
                substrate="Rab10",
                product="phospho-Rab10 (Thr73)",
                cofactor="Mg2+-ATP",
                reaction_type="Ser/Thr phosphorylation",
            ),
        ],
    )


def _build_gsk3b_evidence() -> EvidencePackage:
    """
    GSK-3β — Glycogen synthase kinase-3 beta
    Alzheimer's Disease | tau kinase | EC 2.7.11.26
    Key role: hyperphosphorylation of tau at Ser396, Thr231
    """
    return EvidencePackage(
        gene_symbol="GSK3B",
        metadata=MetadataInfo(
            gene_symbol="GSK3B",
            enzyme_name="Glycogen synthase kinase-3 beta",
            uniprot_id="P49841",
            ec_number="2.7.11.26",
        ),
        disease=DiseaseInfo(
            indication="Alzheimer's Disease",
            target_form="Tau kinase — hyperactive in AD brain",
            clinical_stage="Phase 2 — Tideglusib (non-ATP-competitive GSK-3β inhibitor)",
        ),
        substrates=[
            "Tau protein (Ser396, Thr231, Ser202, Thr205)",
            "Glycogen synthase (Ser641)",
            "β-catenin (Ser33/Ser37/Thr41)",
            "Cyclin D1",
            "eIF2B",
        ],
        products=[
            "Phospho-tau (neurofibrillary tangle precursor)",
            "Phospho-glycogen synthase (inactivated)",
            "Phospho-β-catenin (ubiquitin-targeted)",
        ],
        cofactors=["Mg2+", "ATP"],
        pathogenic_variants=[
            "Overexpression in AD neurons",
            "Y216 autophosphorylation (activation mark)",
        ],
        inhibitors=[
            "Tideglusib (Ki = 5 nM, non-ATP-competitive)",
            "SB216763 (Ki = 34 nM, ATP-competitive)",
            "SB415286 (Ki = 78 nM)",
            "Lithium chloride (IC50 = 2 mM, uncompetitive vs ATP)",
        ],
        mutation_evidence=[
            MutationEvidence(
                position=216,
                wildtype_aa="Y",
                mutant_aa="F",
                mutation_type="moderate",
                cosine_similarity=0.88,
                euclidean_distance=0.38,
                delta_norm=0.32,
                pathogenic=False,
            ),
            MutationEvidence(
                position=9,
                wildtype_aa="S",
                mutant_aa="A",
                mutation_type="benign",
                cosine_similarity=0.95,
                euclidean_distance=0.18,
                delta_norm=0.12,
                pathogenic=False,
            ),
        ],
        kinetic_evidence=[
            KineticEvidence(
                parameter="Km(ATP)",
                value=17.0,
                unit="µM",
                note="Michaelis constant for ATP",
            ),
            KineticEvidence(
                parameter="Km(tau-peptide)",
                value=100.0,
                unit="µM",
                note="Km for primed tau-peptide substrate",
            ),
            KineticEvidence(
                parameter="kcat",
                value=8.2,
                unit="s⁻¹",
                note="Catalytic turnover (phosphorylation of primed substrate)",
            ),
            KineticEvidence(
                parameter="kcat/Km",
                value=82.0,
                unit="mM⁻¹·s⁻¹",
                note="Catalytic efficiency toward primed substrate",
            ),
            KineticEvidence(
                parameter="Ki(SB216763)",
                value=34.0,
                unit="nM",
                note="ATP-competitive inhibitor potency",
            ),
            KineticEvidence(
                parameter="Ki(Tideglusib)",
                value=5.0,
                unit="nM",
                note="Irreversible non-ATP-competitive inhibitor",
            ),
        ],
        reaction_evidence=[
            ReactionEvidence(
                substrate="Tau (Ser396)",
                product="Phospho-tau Ser396",
                cofactor="Mg2+-ATP",
                reaction_type="Ser/Thr phosphorylation",
            ),
            ReactionEvidence(
                substrate="β-catenin (Ser33/37/Thr41)",
                product="Phospho-β-catenin → ubiquitination → degradation",
                cofactor="Mg2+-ATP",
                reaction_type="Ser/Thr phosphorylation (priming requires CK1)",
            ),
        ],
    )


def _build_bace1_evidence() -> EvidencePackage:
    """
    BACE1 — Beta-site APP cleaving enzyme 1 (β-secretase)
    Alzheimer's Disease | aspartyl protease | EC 3.4.23.46
    Cleaves APP at the β-site to initiate Aβ peptide production.
    """
    return EvidencePackage(
        gene_symbol="BACE1",
        metadata=MetadataInfo(
            gene_symbol="BACE1",
            enzyme_name="Beta-site amyloid precursor protein cleaving enzyme 1",
            uniprot_id="P56817",
            ec_number="3.4.23.46",
        ),
        disease=DiseaseInfo(
            indication="Alzheimer's Disease",
            target_form="β-secretase — rate-limiting step in Aβ production",
            clinical_stage=(
                "Phase 3 terminated — Verubecestat (MK-8931) failed 2018; "
                "Atabecestat failed 2018; class-wide liver toxicity concern"
            ),
        ),
        substrates=[
            "Amyloid precursor protein (APP, Swedish mutation KM670/671NL site)",
            "APP wildtype (β-site: Met671-Asp672)",
            "Neuregulin-1 (NRG1)",
            "Seizure-related gene 6 (SEZ6)",
            "CHL1 (close homolog of L1)",
        ],
        products=[
            "sAPPβ (soluble ectodomain)",
            "β-CTF / C99 (substrate for γ-secretase → Aβ40/42)",
            "NRG1 ectodomain (shed fragment)",
        ],
        cofactors=["None — aspartyl protease uses catalytic Asp dyad (Asp93, Asp289)"],
        pathogenic_variants=[
            "APP A673T (Iceland mutation) — protective, reduces BACE1 cleavage by 40%",
            "APP KM670/671NL (Swedish) — hypersubstrate, 6× elevated Aβ production",
            "BACE1 L776V — rare coding variant, elevated activity",
        ],
        inhibitors=[
            "Verubecestat (IC50 = 2.2 nM)",
            "Atabecestat (IC50 = 0.9 nM)",
            "Elenbecestat (IC50 = 3.1 nM)",
            "LY2886721 (IC50 = 18 nM)",
            "OM99-2 (peptidomimetic, Ki = 1.6 nM, research tool)",
        ],
        mutation_evidence=[
            MutationEvidence(
                position=673,
                wildtype_aa="A",
                mutant_aa="T",
                mutation_type="benign",
                cosine_similarity=0.94,
                euclidean_distance=0.22,
                delta_norm=0.15,
                pathogenic=False,
            ),
            MutationEvidence(
                position=671,
                wildtype_aa="M",
                mutant_aa="L",
                mutation_type="moderate",
                cosine_similarity=0.89,
                euclidean_distance=0.41,
                delta_norm=0.38,
                pathogenic=False,
            ),
            MutationEvidence(
                position=776,
                wildtype_aa="L",
                mutant_aa="V",
                mutation_type="disruptive",
                cosine_similarity=0.72,
                euclidean_distance=0.88,
                delta_norm=0.79,
                pathogenic=True,
            ),
        ],
        kinetic_evidence=[
            KineticEvidence(
                parameter="Km(APP-WT peptide)",
                value=12.0,
                unit="µM",
                note="Michaelis constant for wildtype APP β-site peptide",
            ),
            KineticEvidence(
                parameter="Km(APP-Swedish peptide)",
                value=1.8,
                unit="µM",
                note="~6.7× higher affinity for Swedish mutant peptide",
            ),
            KineticEvidence(
                parameter="kcat",
                value=2.1,
                unit="s⁻¹",
                note="Catalytic turnover on APP-WT substrate at pH 4.5",
            ),
            KineticEvidence(
                parameter="kcat/Km(Swedish)",
                value=1167.0,
                unit="mM⁻¹·s⁻¹",
                note="Catalytic efficiency for Swedish mutant substrate",
            ),
            KineticEvidence(
                parameter="Ki(Verubecestat)",
                value=2.2,
                unit="nM",
                note="Competitive inhibitor — Phase 3 failed (cognitive worsening)",
            ),
            KineticEvidence(
                parameter="Optimal pH",
                value=4.5,
                unit="pH units",
                note="Maximal activity in late endosome/lysosome compartment",
            ),
        ],
        reaction_evidence=[
            ReactionEvidence(
                substrate="APP (β-site)",
                product="sAPPβ + β-CTF (C99)",
                cofactor=None,
                reaction_type="Aspartyl protease cleavage (Asp93/Asp289 dyad)",
            ),
            ReactionEvidence(
                substrate="NRG1",
                product="NRG1 ectodomain (EGF-like domain shed)",
                cofactor=None,
                reaction_type="Ectodomain shedding",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# MAO-B evidence builder (for drug selectivity question)
# ---------------------------------------------------------------------------

def _build_maob_evidence() -> EvidencePackage:
    """
    MAO-B — Monoamine oxidase B
    Parkinson's Disease | FAD-dependent oxidase | EC 1.4.3.4
    Degrades dopamine; selective MAO-B inhibitors reduce dopamine catabolism.
    Active site: Tyr435, Tyr398 (aromatic cage) + FAD cofactor (C4a)
    """
    return EvidencePackage(
        gene_symbol="MAOB",
        metadata=MetadataInfo(
            gene_symbol="MAOB",
            enzyme_name="Amine oxidase [flavin-containing] B",
            uniprot_id="P27338",
            ec_number="1.4.3.4",
        ),
        disease=DiseaseInfo(
            indication="Parkinson's Disease",
            target_form="Overexpressed MAO-B accelerates dopamine catabolism in nigrostriatal neurons",
            clinical_stage="Approved — Selegiline (Phase 4), Rasagiline (Phase 4), Safinamide (Phase 4)",
        ),
        substrates=["Dopamine", "Benzylamine", "β-Phenylethylamine (PEA)", "Tyramine"],
        products=["3,4-Dihydroxyphenylacetaldehyde (DOPAL) + H₂O₂", "Benzaldehyde + NH₃ + H₂O₂"],
        cofactors=["FAD (flavin adenine dinucleotide, covalently bound at Cys397)"],
        pathogenic_variants=[
            "MAO-B overexpression with age (2-4× increase in striatum)",
            "rs1799836 A/G SNP — associated with altered MAO-B levels",
        ],
        inhibitors=[
            "Selegiline (IC50 = 0.04 nM, irreversible, propargylamine)",
            "Rasagiline (IC50 = 0.41 nM, irreversible, propargylamine)",
            "Safinamide (IC50 = 0.98 nM, reversible)",
            "Lazabemide (IC50 = 42 nM, reversible, selective)",
            "Clorgyline (MAO-A selective, not MAO-B)",
        ],
        mutation_evidence=[
            MutationEvidence(
                position=435,
                wildtype_aa="Y",
                mutant_aa="F",
                mutation_type="moderate",
                cosine_similarity=0.87,
                euclidean_distance=0.42,
                delta_norm=0.35,
                pathogenic=False,
            ),
            MutationEvidence(
                position=398,
                wildtype_aa="Y",
                mutant_aa="L",
                mutation_type="disruptive",
                cosine_similarity=0.64,
                euclidean_distance=0.98,
                delta_norm=0.88,
                pathogenic=True,
            ),
        ],
        kinetic_evidence=[
            KineticEvidence(
                parameter="Km(dopamine)",
                value=150.0,
                unit="µM",
                note="Michaelis constant for dopamine (MAO-B)",
            ),
            KineticEvidence(
                parameter="kcat",
                value=1.8,
                unit="s⁻¹",
                note="Catalytic turnover for dopamine oxidation",
            ),
            KineticEvidence(
                parameter="Ki(Rasagiline)",
                value=0.41,
                unit="nM",
                note="Irreversible propargylamine — forms covalent adduct with FAD N5",
            ),
            KineticEvidence(
                parameter="Ki(Safinamide)",
                value=0.98,
                unit="nM",
                note="Reversible competitive inhibitor — binds substrate cavity and entrance cavity",
            ),
            KineticEvidence(
                parameter="Active-site cavity volume",
                value=700.0,
                unit="Å³",
                note="MAO-B bipartite cavity (substrate + entrance): larger than MAO-A (490 Å³)",
            ),
        ],
        reaction_evidence=[
            ReactionEvidence(
                substrate="Dopamine",
                product="DOPAL + NH₃ + H₂O₂",
                cofactor="FAD",
                reaction_type="Oxidative deamination (FAD-dependent)",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Question bank
# ---------------------------------------------------------------------------

def build_question_bank() -> List[EvalQuestion]:
    """Return the complete fixed set of evaluation questions."""
    lrrk2 = _build_lrrk2_evidence()
    gsk3b = _build_gsk3b_evidence()
    bace1 = _build_bace1_evidence()
    maob  = _build_maob_evidence()

    return [
        EvalQuestion(
            question_id="Q1",
            text=(
                "Explain the disease relevance of the LRRK2 G2019S variant in "
                "Parkinson's Disease. How does the kinase gain-of-function "
                "mechanistically contribute to neurodegeneration, and what makes "
                "it a therapeutic target?"
            ),
            enzyme="LRRK2",
            mutation="G2019S",
            evidence=lrrk2,
        ),
        EvalQuestion(
            question_id="Q2",
            text=(
                "Interpret the kinetic parameters of GSK-3β (Km, kcat, kcat/Km) "
                "and explain their therapeutic implications for Alzheimer's Disease. "
                "How do the inhibitor potencies (SB216763, Tideglusib) relate to "
                "these kinetics?"
            ),
            enzyme="GSK3B",
            mutation=None,
            evidence=gsk3b,
        ),
        EvalQuestion(
            question_id="Q3",
            text=(
                "What is the mutation impact of the BACE1 L776V variant on "
                "amyloid precursor protein processing? Compare it to the "
                "protective APP A673T mutation and explain the mechanistic "
                "basis of both."
            ),
            enzyme="BACE1",
            mutation="L776V",
            evidence=bace1,
        ),
        EvalQuestion(
            question_id="Q4",
            text=(
                "How does LRRK2 hyperphosphorylation of Rab GTPases (Rab8A, Rab10) "
                "contribute to lysosomal dysfunction and alpha-synuclein accumulation "
                "in Parkinson's Disease? Reference the supplied kinetic and mutation "
                "evidence to support your explanation."
            ),
            enzyme="LRRK2",
            mutation="G2019S",
            evidence=lrrk2,
        ),
        EvalQuestion(
            question_id="Q5",
            text=(
                "Synthesize the mechanistic relationship between GSK-3β-mediated "
                "tau hyperphosphorylation at Ser396 and Thr231, neurofibrillary "
                "tangle formation, and neuronal death in Alzheimer's Disease. "
                "Evaluate whether the catalytic efficiency (kcat/Km = 82 mM⁻¹·s⁻¹) "
                "supports GSK-3β as a high-priority drug target."
            ),
            enzyme="GSK3B",
            mutation=None,
            evidence=gsk3b,
        ),

        # ── Drug Active-Site & Drug-Ability Questions (Q6-Q8) ───────────────

        EvalQuestion(
            question_id="Q6",
            text=(
                "Describe the BACE1 active-site architecture and explain how its "
                "catalytic aspartyl dyad (Asp93/Asp289) enables substrate cleavage. "
                "How do competitive inhibitors like Verubecestat (Ki = 2.2 nM) and "
                "OM99-2 (Ki = 1.6 nM) exploit the active-site geometry to block APP "
                "processing? Why did this drug class fail clinically despite picomolar "
                "potency?"
            ),
            enzyme="BACE1",
            mutation=None,
            evidence=bace1,
        ),
        EvalQuestion(
            question_id="Q7",
            text=(
                "MAO-B inhibitors like Rasagiline and Safinamide are approved for "
                "Parkinson's Disease but differ fundamentally in their binding mode "
                "at the active site. Using the kinetic evidence (Ki values, active-site "
                "cavity volume, FAD cofactor), explain: "
                "(1) how irreversible propargylamine inhibitors form a covalent adduct "
                "with FAD-N5 at the active site; "
                "(2) how reversible inhibitors like Safinamide occupy the substrate "
                "and entrance cavities; "
                "(3) what the 700 Å³ bipartite cavity implies about MAO-B drug selectivity "
                "compared to MAO-A (490 Å³)."
            ),
            enzyme="MAOB",
            mutation=None,
            evidence=maob,
        ),
        EvalQuestion(
            question_id="Q8",
            text=(
                "Compare the drug-ability of three neurological enzyme targets — "
                "LRRK2 (kinase), BACE1 (aspartyl protease), and MAO-B (FAD-oxidase) "
                "— using the supplied evidence packages. For each: "
                "(1) identify the active-site residues or cofactors that drugs exploit; "
                "(2) state the most potent approved or clinical inhibitor and its IC50/Ki; "
                "(3) assess why each target succeeded or failed as a drug target based "
                "on mechanism-of-action and clinical outcome evidence provided."
            ),
            enzyme="LRRK2",
            mutation=None,
            evidence=lrrk2,
        ),
    ]


# Convenience mapping
QUESTION_BANK: List[EvalQuestion] = build_question_bank()
QUESTION_BY_ID: Dict[str, EvalQuestion] = {q.question_id: q for q in QUESTION_BANK}


def get_questions(ids: Optional[List[str]] = None) -> List[EvalQuestion]:
    """Return questions filtered by IDs (e.g. ['Q1', 'Q3']), or all if ids is None."""
    if ids is None:
        return QUESTION_BANK
    return [QUESTION_BY_ID[qid] for qid in ids if qid in QUESTION_BY_ID]
