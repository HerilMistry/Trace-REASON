
from __future__ import annotations
from typing import List
from src.evidence import (
    EvidencePackage, MetadataInfo, DiseaseInfo, MutationEvidence,
    KineticEvidence, ReactionEvidence
)
from eval.questions import EvalQuestion

def _build_egfr_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="EGFR",
        metadata=MetadataInfo(
            gene_symbol="EGFR", enzyme_name="Epidermal growth factor receptor",
            uniprot_id="P00533", ec_number="2.7.10.1"
        ),
        disease=DiseaseInfo(
            indication="Non-Small Cell Lung Cancer (NSCLC)",
            target_form="Activating mutations in kinase domain",
            clinical_stage="Approved (Osimertinib, Gefitinib, Erlotinib)"
        ),
        substrates=["ATP", "Tyrosine residues on target proteins"],
        products=["ADP", "Phospho-tyrosine"],
        cofactors=["Mg2+", "Mn2+"],
        pathogenic_variants=["L858R", "T790M", "C797S"],
        inhibitors=["Osimertinib", "Gefitinib", "Erlotinib"],
        mutation_evidence=[
            MutationEvidence(position=858, wildtype_aa="L", mutant_aa="R", mutation_type="activating", cosine_similarity=0.6, euclidean_distance=1.0, delta_norm=0.9, pathogenic=True),
            MutationEvidence(position=790, wildtype_aa="T", mutant_aa="M", mutation_type="resistance", cosine_similarity=0.8, euclidean_distance=0.5, delta_norm=0.4, pathogenic=True),
            MutationEvidence(position=797, wildtype_aa="C", mutant_aa="S", mutation_type="resistance", cosine_similarity=0.9, euclidean_distance=0.3, delta_norm=0.2, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_abl1_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="ABL1",
        metadata=MetadataInfo(
            gene_symbol="ABL1", enzyme_name="Tyrosine-protein kinase ABL1",
            uniprot_id="P00519", ec_number="2.7.10.2"
        ),
        disease=DiseaseInfo(
            indication="Chronic Myeloid Leukemia (CML)",
            target_form="BCR-ABL1 fusion protein",
            clinical_stage="Approved (Imatinib, Dasatinib, Ponatinib)"
        ),
        substrates=["ATP", "Tyrosine residues"],
        products=["ADP", "Phospho-tyrosine"], cofactors=["Mg2+"],
        pathogenic_variants=["T315I"],
        inhibitors=["Imatinib", "Ponatinib"],
        mutation_evidence=[
            MutationEvidence(position=315, wildtype_aa="T", mutant_aa="I", mutation_type="resistance", cosine_similarity=0.7, euclidean_distance=0.8, delta_norm=0.7, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_braf_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="BRAF",
        metadata=MetadataInfo(
            gene_symbol="BRAF", enzyme_name="Serine/threonine-protein kinase B-raf",
            uniprot_id="P15056", ec_number="2.7.11.1"
        ),
        disease=DiseaseInfo(
            indication="Melanoma",
            target_form="V600E activating mutation",
            clinical_stage="Approved (Vemurafenib, Dabrafenib)"
        ),
        substrates=["ATP", "MEK1/2"], products=["ADP", "Phospho-MEK"], cofactors=["Mg2+"],
        pathogenic_variants=["V600E"], inhibitors=["Vemurafenib"],
        mutation_evidence=[
            MutationEvidence(position=600, wildtype_aa="V", mutant_aa="E", mutation_type="activating", cosine_similarity=0.5, euclidean_distance=1.2, delta_norm=1.0, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_idh1_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="IDH1",
        metadata=MetadataInfo(
            gene_symbol="IDH1", enzyme_name="Isocitrate dehydrogenase [NADP] cytoplasmic",
            uniprot_id="O75874", ec_number="1.1.1.42"
        ),
        disease=DiseaseInfo(
            indication="Glioma / AML",
            target_form="Neomorphic mutation (produces 2-HG)",
            clinical_stage="Approved (Ivosidenib)"
        ),
        substrates=["Isocitrate", "NADP+ (wildtype)", "alpha-KG (mutant)"],
        products=["alpha-KG", "NADPH (wildtype)", "D-2-hydroxyglutarate (mutant)"], cofactors=["Mg2+", "Mn2+"],
        pathogenic_variants=["R132H"], inhibitors=["Ivosidenib"],
        mutation_evidence=[
            MutationEvidence(position=132, wildtype_aa="R", mutant_aa="H", mutation_type="neomorphic", cosine_similarity=0.6, euclidean_distance=0.9, delta_norm=0.85, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_idh2_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="IDH2",
        metadata=MetadataInfo(
            gene_symbol="IDH2", enzyme_name="Isocitrate dehydrogenase [NADP], mitochondrial",
            uniprot_id="P48735", ec_number="1.1.1.42"
        ),
        disease=DiseaseInfo(
            indication="AML",
            target_form="Neomorphic mutation",
            clinical_stage="Approved (Enasidenib)"
        ),
        substrates=["Isocitrate", "NADP+", "alpha-KG (mutant)"],
        products=["alpha-KG", "NADPH", "D-2-hydroxyglutarate (mutant)"], cofactors=["Mg2+", "Mn2+"],
        pathogenic_variants=["R140Q", "R172K"], inhibitors=["Enasidenib"],
        mutation_evidence=[
            MutationEvidence(position=140, wildtype_aa="R", mutant_aa="Q", mutation_type="neomorphic", cosine_similarity=0.7, euclidean_distance=0.8, delta_norm=0.75, pathogenic=True),
            MutationEvidence(position=172, wildtype_aa="R", mutant_aa="K", mutation_type="neomorphic", cosine_similarity=0.7, euclidean_distance=0.8, delta_norm=0.75, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_pik3ca_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="PIK3CA",
        metadata=MetadataInfo(
            gene_symbol="PIK3CA", enzyme_name="Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit alpha",
            uniprot_id="P42336", ec_number="2.7.1.153"
        ),
        disease=DiseaseInfo(
            indication="Breast Cancer",
            target_form="Activating mutation",
            clinical_stage="Approved (Alpelisib)"
        ),
        substrates=["ATP", "PIP2"], products=["ADP", "PIP3"], cofactors=["Mg2+"],
        pathogenic_variants=["H1047R", "E545K"], inhibitors=["Alpelisib"],
        mutation_evidence=[
            MutationEvidence(position=1047, wildtype_aa="H", mutant_aa="R", mutation_type="activating", cosine_similarity=0.65, euclidean_distance=0.9, delta_norm=0.8, pathogenic=True),
            MutationEvidence(position=545, wildtype_aa="E", mutant_aa="K", mutation_type="activating", cosine_similarity=0.6, euclidean_distance=0.95, delta_norm=0.85, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_flt3_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="FLT3",
        metadata=MetadataInfo(
            gene_symbol="FLT3", enzyme_name="Receptor-type tyrosine-protein kinase FLT3",
            uniprot_id="P36888", ec_number="2.7.10.1"
        ),
        disease=DiseaseInfo(
            indication="AML",
            target_form="Activating mutation",
            clinical_stage="Approved (Midostaurin, Gilteritinib)"
        ),
        substrates=["ATP", "Tyrosine residues"], products=["ADP", "Phospho-tyrosine"], cofactors=["Mg2+"],
        pathogenic_variants=["D835Y", "ITD"], inhibitors=["Midostaurin", "Gilteritinib"],
        mutation_evidence=[
            MutationEvidence(position=835, wildtype_aa="D", mutant_aa="Y", mutation_type="activating", cosine_similarity=0.55, euclidean_distance=1.1, delta_norm=0.95, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_pink1_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="PINK1",
        metadata=MetadataInfo(
            gene_symbol="PINK1", enzyme_name="PTEN-induced kinase 1",
            uniprot_id="Q9BXM7", ec_number="2.7.11.1"
        ),
        disease=DiseaseInfo(
            indication="Parkinson's Disease",
            target_form="Loss-of-function",
            clinical_stage="Preclinical"
        ),
        substrates=["ATP", "Ubiquitin", "Parkin"], products=["ADP", "Phospho-ubiquitin"], cofactors=["Mg2+"],
        pathogenic_variants=["G309D", "Q456X"], inhibitors=[],
        mutation_evidence=[
            MutationEvidence(position=309, wildtype_aa="G", mutant_aa="D", mutation_type="loss-of-function", cosine_similarity=0.4, euclidean_distance=1.3, delta_norm=1.1, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_psen1_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="PSEN1",
        metadata=MetadataInfo(
            gene_symbol="PSEN1", enzyme_name="Presenilin-1",
            uniprot_id="P49768", ec_number="3.4.23.46"
        ),
        disease=DiseaseInfo(
            indication="Alzheimer's Disease",
            target_form="Familial AD mutation",
            clinical_stage="Clinical/Research"
        ),
        substrates=["APP"], products=["Abeta 42"], cofactors=[],
        pathogenic_variants=["E280A", "M146L"], inhibitors=["Gamma-secretase inhibitors"],
        mutation_evidence=[
            MutationEvidence(position=280, wildtype_aa="E", mutant_aa="A", mutation_type="pathogenic", cosine_similarity=0.7, euclidean_distance=0.8, delta_norm=0.7, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def _build_gba1_evidence() -> EvidencePackage:
    return EvidencePackage(
        gene_symbol="GBA1",
        metadata=MetadataInfo(
            gene_symbol="GBA1", enzyme_name="Glucosylceramidase",
            uniprot_id="P04062", ec_number="3.2.1.45"
        ),
        disease=DiseaseInfo(
            indication="Gaucher Disease",
            target_form="Loss-of-function",
            clinical_stage="Approved (Imiglucerase)"
        ),
        substrates=["Glucosylceramide"], products=["Glucose", "Ceramide"], cofactors=[],
        pathogenic_variants=["N370S", "L444P"], inhibitors=["Miglustat (SRT)"],
        mutation_evidence=[
            MutationEvidence(position=370, wildtype_aa="N", mutant_aa="S", mutation_type="loss-of-function", cosine_similarity=0.75, euclidean_distance=0.6, delta_norm=0.5, pathogenic=True)
        ],
        kinetic_evidence=[], reaction_evidence=[]
    )

def build_mutation_questions() -> List[EvalQuestion]:
    egfr = _build_egfr_evidence()
    abl1 = _build_abl1_evidence()
    braf = _build_braf_evidence()
    idh1 = _build_idh1_evidence()
    idh2 = _build_idh2_evidence()
    pik3ca = _build_pik3ca_evidence()
    flt3 = _build_flt3_evidence()
    pink1 = _build_pink1_evidence()
    psen1 = _build_psen1_evidence()
    gba1 = _build_gba1_evidence()

    return [
        EvalQuestion("Q9", "How does the EGFR L858R mutation lead to constitutive activation in NSCLC, and why does the subsequent T790M mutation confer resistance to first-generation inhibitors like gefitinib?", "EGFR", "L858R/T790M", egfr),
        EvalQuestion("Q10", "Explain how the C797S mutation in EGFR mediates resistance to osimertinib by altering the active-site geometry.", "EGFR", "C797S", egfr),
        EvalQuestion("Q11", "Discuss the mechanism by which the BCR-ABL1 T315I mutation prevents imatinib binding in CML. Why is ponatinib effective against this variant?", "ABL1", "T315I", abl1),
        EvalQuestion("Q12", "How does the BRAF V600E mutation mimic regulatory phosphorylation to cause constitutive kinase activity in melanoma? What is the rationale for using vemurafenib?", "BRAF", "V600E", braf),
        EvalQuestion("Q13", "Explain the neomorphic activity of the IDH1 R132H mutation in glioma. How does the production of D-2-hydroxyglutarate contribute to oncogenesis?", "IDH1", "R132H", idh1),
        EvalQuestion("Q14", "Compare the neomorphic mutations R140Q and R172K in IDH2. How does enasidenib target these mutant forms in AML?", "IDH2", "R140Q/R172K", idh2),
        EvalQuestion("Q15", "Describe how the PIK3CA H1047R and E545K mutations activate the PI3K/AKT pathway in breast cancer. What makes alpelisib selective for the alpha isoform?", "PIK3CA", "H1047R/E545K", pik3ca),
        EvalQuestion("Q16", "How do FLT3 D835Y and internal tandem duplications (ITD) drive AML, and what is the binding mode of midostaurin in inhibiting these mutants?", "FLT3", "D835Y/ITD", flt3),
        EvalQuestion("Q17", "What are the structural consequences of the PINK1 G309D mutation, and how does this loss-of-function variant impair mitophagy in Parkinson's disease?", "PINK1", "G309D", pink1),
        EvalQuestion("Q18", "Explain the effect of the PINK1 Q456X truncation on kinase stability and its association with early-onset Parkinson's disease.", "PINK1", "Q456X", pink1),
        EvalQuestion("Q19", "How does the PSEN1 E280A founder mutation alter gamma-secretase processing of APP, and what are its implications for amyloid-beta 42 production in Alzheimer's disease?", "PSEN1", "E280A", psen1),
        EvalQuestion("Q20", "Discuss the pathogenic mechanism of the PSEN1 M146L mutation in familial Alzheimer's disease and its impact on catalytic function.", "PSEN1", "M146L", psen1),
        EvalQuestion("Q21", "How do the GBA1 N370S and L444P mutations reduce glucocerebrosidase activity, and how do they differ in clinical severity for Gaucher disease?", "GBA1", "N370S/L444P", gba1),
        EvalQuestion("Q22", "Explain the link between GBA1 mutations (like N370S) and increased risk for Parkinson's disease through lysosomal dysfunction.", "GBA1", "N370S", gba1),
        EvalQuestion("Q23", "Compare the therapeutic strategies of enzyme replacement therapy (imiglucerase) versus substrate reduction therapy for patients with GBA1 mutations.", "GBA1", "Mutations", gba1),
    ]
