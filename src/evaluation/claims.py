import json
import os
from typing import List, Dict, Any
from src.llm import LLMFactory
from src.evidence import EvidencePackage

class ClaimEvaluator:
    def __init__(self, llm_provider="groq"):
        self.llm = LLMFactory.create_provider(llm_provider)
        self.evaluations_dir = "outputs/evaluations"
        os.makedirs(self.evaluations_dir, exist_ok=True)

    def extract_claims(self, explanation: str) -> List[str]:
        prompt = f"""
        Extract all atomic, verifiable scientific claims from the following explanation.
        Each claim should be a single, standalone sentence.
        
        Explanation:
        {explanation}
        """
        response = self.llm.structured_query(prompt, {
            "claims": ["string"]
        })
        return response.get("claims", [])

    def verify_claims(self, claims: List[str], evidence: EvidencePackage) -> List[Dict[str, Any]]:
        evidence_summary = evidence.get_summary()
        
        results = []
        for claim in claims:
            prompt = f"""
            Verify the following scientific claim using the provided evidence.
            
            Claim: {claim}
            
            Evidence Summary:
            {evidence_summary}
            
            Determine the verification status exactly as one of the following:
            - "supported": if the evidence fully supports the claim
            - "partially supported": if the evidence supports part of the claim
            - "unsupported": if the evidence does not support or contradicts the claim
            """
            
            response = self.llm.structured_query(prompt, {
                "status": "string",
                "reasoning": "string"
            })
            
            status = response.get("status", "unsupported").lower()
            if status not in ["supported", "partially supported", "unsupported"]:
                status = "unsupported"
                
            results.append({
                "claim": claim,
                "status": status,
                "reasoning": response.get("reasoning", "")
            })
            
        return results

    def evaluate_explanation(self, explanation: str, evidence: EvidencePackage, identifier: str) -> Dict[str, Any]:
        claims = self.extract_claims(explanation)
        verifications = self.verify_claims(claims, evidence)
        
        supported = sum(1 for v in verifications if v["status"] == "supported")
        unsupported = sum(1 for v in verifications if v["status"] == "unsupported")
        total = len(verifications)
        
        result = {
            "identifier": identifier,
            "total_claims": total,
            "supported_claims": supported,
            "unsupported_claims": unsupported,
            "faithfulness": supported / total if total > 0 else 0.0,
            "hallucination_rate": unsupported / total if total > 0 else 0.0,
            "verifications": verifications
        }
        
        output_path = os.path.join(self.evaluations_dir, f"claim_verification_{identifier}.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
            
        return result
