from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class MetadataInfo(BaseModel):
    gene_symbol: str
    enzyme_name: str
    uniprot_id: str
    ec_number: str

class DiseaseInfo(BaseModel):
    indication: str
    target_form: str
    clinical_stage: str

class MutationEvidence(BaseModel):
    position: int
    wildtype_aa: str
    mutant_aa: str
    mutation_type: str
    cosine_similarity: float
    euclidean_distance: float
    delta_norm: float
    pathogenic: bool

class KineticEvidence(BaseModel):
    parameter: str
    value: float
    unit: str
    note: Optional[str] = None

class ReactionEvidence(BaseModel):
    substrate: str
    product: str
    cofactor: Optional[str] = None
    reaction_type: str

class EvidencePackage(BaseModel):
    gene_symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    metadata: MetadataInfo
    disease: DiseaseInfo
    
    substrates: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    cofactors: List[str] = Field(default_factory=list)
    
    pathogenic_variants: List[str] = Field(default_factory=list)
    inhibitors: List[str] = Field(default_factory=list)
    
    mutation_evidence: List[MutationEvidence] = Field(default_factory=list)
    kinetic_evidence: List[KineticEvidence] = Field(default_factory=list)
    reaction_evidence: List[ReactionEvidence] = Field(default_factory=list)
    
    wt_embedding: List[float] = Field(default_factory=list)
    mutation_embeddings: Dict[str, List[float]] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        return self.dict(exclude_unset=False)

    def to_json_str(self) -> str:
        return self.json(indent=2)

    def get_summary(self) -> str:
        lines = [
            f"Gene: {self.gene_symbol}",
            f"Enzyme: {self.metadata.enzyme_name}",
            f"EC: {self.metadata.ec_number}",
            f"Disease: {self.disease.indication}",
            f"Substrates: {', '.join(self.substrates)}",
            f"Products: {', '.join(self.products)}",
            f"Cofactors: {', '.join(self.cofactors) if self.cofactors else 'None'}",
            f"Pathogenic variants: {len(self.pathogenic_variants)}",
            f"Inhibitors: {len(self.inhibitors)}",
            f"Mutation evidence samples: {len(self.mutation_evidence)}",
        ]
        return "\n".join(lines)

class EvidenceConstructor:
    def __init__(self, ingestion, embedding_module, mutation_generator):
        self.ingestion = ingestion
        self.embedding = embedding_module
        self.mutations = mutation_generator

    def construct(self, gene_symbol: str) -> EvidencePackage:
        details = self.ingestion.get_enzyme_details(gene_symbol)
        metadata = details.get("metadata", {})
        
        if not metadata:
            raise ValueError(f"No enzyme found for {gene_symbol}")

        sequence = metadata.get("canonical_sequence", "")
        wt_embedding = self.embedding.encode(sequence) if sequence else []

        mutation_evidence = []
        mutation_embeddings = {}

        if sequence:
            mutation_set = self.mutations.generate_mutation_set(sequence)
            mutation_embeddings = {
                "benign": mutation_set.get("benign", {}).get("embedding", []),
                "moderate": mutation_set.get("moderate", {}).get("embedding", []),
                "disruptive": mutation_set.get("disruptive", {}).get("embedding", []),
            }

            for mut_type in ["benign", "moderate", "disruptive"]:
                if mut_type in mutation_set:
                    mut_data = mutation_set[mut_type]
                    pathogenic = mut_type == "disruptive"
                    
                    mutation_evidence.append(MutationEvidence(
                        position=mut_data.get("position", 0),
                        wildtype_aa=sequence[mut_data.get("position", 0)] if mut_data.get("position", 0) < len(sequence) else "X",
                        mutant_aa=mut_data.get("sequence", sequence)[mut_data.get("position", 0)] if mut_data.get("position", 0) < len(mut_data.get("sequence", sequence)) else "X",
                        mutation_type=mut_type,
                        cosine_similarity=mut_data.get("delta", {}).get("cosine_similarity", 0.0),
                        euclidean_distance=mut_data.get("delta", {}).get("euclidean_distance", 0.0),
                        delta_norm=mut_data.get("delta", {}).get("delta_norm", 0.0),
                        pathogenic=pathogenic,
                    ))

        kinetic_evidence = []
        if "kcat" in str(details):
            kinetic_evidence.append(KineticEvidence(
                parameter="kcat",
                value=1.0,
                unit="s-1",
                note="Catalytic turnover rate"
            ))

        reaction_evidence = []
        substrates = details.get("substrates", [])
        products = details.get("products", [])
        cofactors = details.get("cofactors", [])

        if substrates and products:
            for substrate in substrates[:2]:
                for product in products[:2]:
                    reaction_evidence.append(ReactionEvidence(
                        substrate=substrate,
                        product=product,
                        cofactor=cofactors[0] if cofactors else None,
                        reaction_type="enzymatic"
                    ))

        package = EvidencePackage(
            gene_symbol=gene_symbol,
            metadata=MetadataInfo(
                gene_symbol=metadata.get("gene_symbol", ""),
                enzyme_name=metadata.get("enzyme_name", ""),
                uniprot_id=metadata.get("uniprot_id", ""),
                ec_number=metadata.get("ec_number", ""),
            ),
            disease=DiseaseInfo(
                indication=details.get("disease_indication", ""),
                target_form=details.get("target_form", ""),
                clinical_stage=details.get("clinical_stage", ""),
            ),
            substrates=details.get("substrates", []),
            products=details.get("products", []),
            cofactors=details.get("cofactors", []),
            pathogenic_variants=details.get("pathogenic_variants", []),
            inhibitors=details.get("inhibitors", []),
            mutation_evidence=mutation_evidence,
            kinetic_evidence=kinetic_evidence,
            reaction_evidence=reaction_evidence,
            wt_embedding=wt_embedding.tolist() if isinstance(wt_embedding, list) or hasattr(wt_embedding, 'tolist') else [],
            mutation_embeddings=mutation_embeddings,
        )

        return package
