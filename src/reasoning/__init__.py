from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json
import os
from src.evidence import EvidencePackage
from src.llm import LLMProvider

class ReasoningNode(BaseModel):
    node_id: str
    node_name: str
    input_data: Dict[str, Any]
    output: Dict[str, Any] = Field(default_factory=dict)
    evidence_used: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning_chain: str = ""

class ReasoningTrace(BaseModel):
    enzyme: str
    nodes: List[ReasoningNode] = Field(default_factory=list)
    final_explanation: str = ""
    completed_nodes: int = 0
    total_nodes: int = 6
    hallucinations: List[str] = Field(default_factory=list)
    supported_claims: int = 0
    total_claims: int = 0

    def get_completion_rate(self) -> float:
        return self.completed_nodes / self.total_nodes if self.total_nodes > 0 else 0.0

    def get_faithfulness(self) -> float:
        return self.supported_claims / self.total_claims if self.total_claims > 0 else 0.0

    def get_hallucination_rate(self) -> float:
        return len(self.hallucinations) / self.total_claims if self.total_claims > 0 else 0.0

    def save_trace(self, identifier: str):
        traces_dir = "outputs/traces"
        os.makedirs(traces_dir, exist_ok=True)
        path = os.path.join(traces_dir, f"{identifier}_trace.json")
        with open(path, "w") as f:
            f.write(self.json(indent=2))

class ReasoningPipeline:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.trace = None

    def node_1_enzyme_identity(self, evidence: EvidencePackage) -> ReasoningNode:
        prompt = f"""
Given this enzyme information, extract and validate enzyme identity:

Gene Symbol: {evidence.gene_symbol}
Enzyme Name: {evidence.metadata.enzyme_name}
UniProt ID: {evidence.metadata.uniprot_id}
EC Number: {evidence.metadata.ec_number}

Provide:
1. Validated identity
2. Enzyme class/type
3. Functional role
4. Confidence score (0-1)

Respond with JSON: {{
    "validated_name": "",
    "enzyme_class": "",
    "functional_role": "",
    "confidence": 0.0,
    "reasoning": ""
}}
"""
        response = self.llm.structured_query(prompt, {
            "validated_name": "string",
            "enzyme_class": "string",
            "functional_role": "string",
            "confidence": "number",
            "reasoning": "string"
        })

        return ReasoningNode(
            node_id="1",
            node_name="Enzyme Identity",
            input_data={"gene_symbol": evidence.gene_symbol, "enzyme_name": evidence.metadata.enzyme_name},
            output=response,
            evidence_used=["metadata"],
            confidence=response.get("confidence", 0.0),
            reasoning_chain=response.get("reasoning", "")
        )

    def node_2_substrate_analysis(self, evidence: EvidencePackage) -> ReasoningNode:
        substrates = "\n".join(evidence.substrates) if evidence.substrates else "Not specified"
        products = "\n".join(evidence.products) if evidence.products else "Not specified"
        
        prompt = f"""
Analyze enzyme substrate specificity and binding:

Enzyme: {evidence.metadata.enzyme_name}
Substrates:
{substrates}

Products:
{products}

Analyze:
1. Substrate recognition mechanism
2. Binding affinity implications
3. Product generation pathway
4. Specificity constraints

Respond with JSON: {{
    "substrate_specificity": "",
    "binding_mechanism": "",
    "product_pathway": "",
    "confidence": 0.0
}}
"""
        response = self.llm.structured_query(prompt, {
            "substrate_specificity": "string",
            "binding_mechanism": "string",
            "product_pathway": "string",
            "confidence": "number"
        })

        return ReasoningNode(
            node_id="2",
            node_name="Substrate Analysis",
            input_data={"substrates": evidence.substrates, "products": evidence.products},
            output=response,
            evidence_used=["substrates", "products"],
            confidence=response.get("confidence", 0.0)
        )

    def node_3_kinetic_interpretation(self, evidence: EvidencePackage) -> ReasoningNode:
        kinetic_info = "\n".join([
            f"{k.parameter}: {k.value} {k.unit}" for k in evidence.kinetic_evidence
        ]) if evidence.kinetic_evidence else "No kinetic data"

        prompt = f"""
Interpret enzyme kinetics:

Enzyme: {evidence.metadata.enzyme_name}

Kinetic Parameters:
{kinetic_info}

Analyze:
1. Catalytic efficiency
2. Turnover rate implications
3. Rate-limiting steps
4. Regulatory potential

Respond with JSON: {{
    "catalytic_efficiency": "",
    "turnover_implications": "",
    "rate_limiting": "",
    "confidence": 0.0
}}
"""
        response = self.llm.structured_query(prompt, {
            "catalytic_efficiency": "string",
            "turnover_implications": "string",
            "rate_limiting": "string",
            "confidence": "number"
        })

        return ReasoningNode(
            node_id="3",
            node_name="Kinetic Interpretation",
            input_data={"kinetic_evidence": [k.dict() for k in evidence.kinetic_evidence]},
            output=response,
            evidence_used=["kinetic_evidence"],
            confidence=response.get("confidence", 0.0)
        )

    def node_4_mutation_impact(self, evidence: EvidencePackage) -> ReasoningNode:
        mutations_info = "\n".join([
            f"{m.mutation_type}: {m.wildtype_aa}{m.position}{m.mutant_aa} (delta_norm={m.delta_norm:.3f}, pathogenic={m.pathogenic})"
            for m in evidence.mutation_evidence
        ]) if evidence.mutation_evidence else "No mutation data"

        prompt = f"""
Analyze mutation impact:

Enzyme: {evidence.metadata.enzyme_name}

Mutation Evidence:
{mutations_info}

Analyze:
1. Impact on enzyme structure
2. Effect on catalytic activity
3. Disease association
4. Prediction confidence

Respond with JSON: {{
    "structure_impact": "",
    "activity_effect": "",
    "disease_link": "",
    "confidence": 0.0
}}
"""
        response = self.llm.structured_query(prompt, {
            "structure_impact": "string",
            "activity_effect": "string",
            "disease_link": "string",
            "confidence": "number"
        })

        return ReasoningNode(
            node_id="4",
            node_name="Mutation Impact",
            input_data={"mutation_evidence": [m.dict() for m in evidence.mutation_evidence]},
            output=response,
            evidence_used=["mutation_evidence"],
            confidence=response.get("confidence", 0.0)
        )

    def node_5_disease_reasoning(self, evidence: EvidencePackage) -> ReasoningNode:
        variants = "\n".join(evidence.pathogenic_variants) if evidence.pathogenic_variants else "Not specified"
        
        prompt = f"""
Connect enzyme to disease pathology:

Enzyme: {evidence.metadata.enzyme_name}
Disease: {evidence.disease.indication}
Target Form: {evidence.disease.target_form}
Clinical Stage: {evidence.disease.clinical_stage}

Pathogenic Variants:
{variants}

Analyze:
1. Enzyme role in disease pathology
2. Therapeutic target rationale
3. Expected clinical benefit
4. Mechanistic plausibility

Respond with JSON: {{
    "pathology_role": "",
    "therapeutic_rationale": "",
    "clinical_benefit": "",
    "confidence": 0.0
}}
"""
        response = self.llm.structured_query(prompt, {
            "pathology_role": "string",
            "therapeutic_rationale": "string",
            "clinical_benefit": "string",
            "confidence": "number"
        })

        return ReasoningNode(
            node_id="5",
            node_name="Disease Reasoning",
            input_data={"disease": evidence.disease.dict(), "variants": evidence.pathogenic_variants},
            output=response,
            evidence_used=["disease", "pathogenic_variants"],
            confidence=response.get("confidence", 0.0)
        )

    def node_6_final_synthesis(self, evidence: EvidencePackage, previous_nodes: List[ReasoningNode]) -> ReasoningNode:
        previous_outputs = "\n".join([
            f"{n.node_name}:\n{n.output}"
            for n in previous_nodes
        ])

        prompt = f"""
Synthesize complete enzyme explanation:

Enzyme: {evidence.metadata.enzyme_name}
Disease: {evidence.disease.indication}

Previous Analysis:
{previous_outputs}

Synthesize:
1. Complete mechanistic explanation
2. Integrated disease connection
3. Overall confidence and uncertainty
4. Key evidence support

Respond with JSON: {{
    "mechanistic_explanation": "",
    "disease_mechanism": "",
    "overall_confidence": 0.0,
    "key_evidence": [],
    "caveats": ""
}}
"""
        response = self.llm.structured_query(prompt, {
            "mechanistic_explanation": "string",
            "disease_mechanism": "string",
            "overall_confidence": "number",
            "key_evidence": "array",
            "caveats": "string"
        })

        return ReasoningNode(
            node_id="6",
            node_name="Final Synthesis",
            input_data={"previous_nodes": [n.node_name for n in previous_nodes]},
            output=response,
            evidence_used=[e for n in previous_nodes for e in n.evidence_used],
            confidence=response.get("overall_confidence", 0.0)
        )

    def execute(self, evidence: EvidencePackage) -> ReasoningTrace:
        trace = ReasoningTrace(enzyme=evidence.gene_symbol)

        node1 = self.node_1_enzyme_identity(evidence)
        trace.nodes.append(node1)
        trace.completed_nodes += 1

        node2 = self.node_2_substrate_analysis(evidence)
        trace.nodes.append(node2)
        trace.completed_nodes += 1

        node3 = self.node_3_kinetic_interpretation(evidence)
        trace.nodes.append(node3)
        trace.completed_nodes += 1

        node4 = self.node_4_mutation_impact(evidence)
        trace.nodes.append(node4)
        trace.completed_nodes += 1

        node5 = self.node_5_disease_reasoning(evidence)
        trace.nodes.append(node5)
        trace.completed_nodes += 1

        node6 = self.node_6_final_synthesis(evidence, trace.nodes)
        trace.nodes.append(node6)
        trace.completed_nodes += 1

        synthesis = node6.output.get("mechanistic_explanation", "")
        trace.final_explanation = synthesis
        trace.supported_claims = sum(1 for node in trace.nodes if node.confidence > 0.5)
        trace.total_claims = len(trace.nodes)

        self.trace = trace
        return trace
