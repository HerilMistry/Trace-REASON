from typing import List, Dict, Any
from src.reasoning import ReasoningTrace
import numpy as np

class EvaluationMetrics:
    @staticmethod
    def calculate_faithfulness(trace: ReasoningTrace, claim_eval_result: Dict[str, Any] = None) -> float:
        if claim_eval_result:
            return claim_eval_result.get("faithfulness", 0.0)
        if trace.total_claims == 0:
            return 0.0
        return trace.supported_claims / trace.total_claims

    @staticmethod
    def calculate_hallucination_rate(trace: ReasoningTrace, claim_eval_result: Dict[str, Any] = None) -> float:
        if claim_eval_result:
            return claim_eval_result.get("hallucination_rate", 0.0)
        if trace.total_claims == 0:
            return 0.0
        return len(trace.hallucinations) / trace.total_claims

    @staticmethod
    def calculate_evidence_utilization(trace: ReasoningTrace) -> float:
        total_evidence_slots = trace.total_nodes * 3
        used_evidence = sum(len(node.evidence_used) for node in trace.nodes)
        if total_evidence_slots == 0:
            return 0.0
        return min(used_evidence / total_evidence_slots, 1.0)

    @staticmethod
    def calculate_trace_completeness(trace: ReasoningTrace) -> float:
        return trace.get_completion_rate()

    @staticmethod
    def calculate_grounding_score(faithfulness: float, evidence_util: float, hallucination_rate: float) -> float:
        return (0.4 * faithfulness) + (0.3 * evidence_util) - (0.3 * hallucination_rate)

    @staticmethod
    def calculate_mutation_sensitivity(baseline_embedding: List[float], mutant_embedding: List[float]) -> float:
        baseline = np.array(baseline_embedding)
        mutant = np.array(mutant_embedding)
        
        cosine_sim = np.dot(baseline, mutant) / (np.linalg.norm(baseline) * np.linalg.norm(mutant))
        return 1.0 - cosine_sim

    @staticmethod
    def calculate_consistency(runs: List[ReasoningTrace]) -> float:
        if len(runs) < 2:
            return 1.0
        
        scores = [EvaluationMetrics.calculate_faithfulness(r) for r in runs]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        if mean_score == 0:
            return 0.0
        coefficient_of_variation = std_score / mean_score
        consistency = 1.0 - min(coefficient_of_variation, 1.0)
        return consistency

    @staticmethod
    def calculate_confidence_calibration(predicted_confidences: List[float], correctness: List[bool]) -> float:
        if len(predicted_confidences) == 0:
            return 0.0
        
        confidences = np.array(predicted_confidences)
        is_correct = np.array(correctness)
        
        num_bins = 10
        bin_edges = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        
        for i in range(num_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if mask.sum() > 0:
                avg_confidence = confidences[mask].mean()
                accuracy = is_correct[mask].mean()
                ece += abs(avg_confidence - accuracy) * mask.sum() / len(confidences)
        
        return 1.0 - ece

    @staticmethod
    def compute_all_metrics(trace: ReasoningTrace, claim_eval_result: Dict[str, Any] = None) -> Dict[str, float]:
        faithfulness = EvaluationMetrics.calculate_faithfulness(trace, claim_eval_result)
        hallucination_rate = EvaluationMetrics.calculate_hallucination_rate(trace, claim_eval_result)
        evidence_utilization = EvaluationMetrics.calculate_evidence_utilization(trace)
        trace_completeness = EvaluationMetrics.calculate_trace_completeness(trace)
        grounding_score = EvaluationMetrics.calculate_grounding_score(faithfulness, evidence_utilization, hallucination_rate)
        
        return {
            "faithfulness": faithfulness,
            "hallucination_rate": hallucination_rate,
            "evidence_utilization": evidence_utilization,
            "trace_completeness": trace_completeness,
            "grounding_score": grounding_score,
        }

class EvaluationResult:
    def __init__(self, enzyme: str, method: str, experiment: str):
        self.enzyme = enzyme
        self.method = method
        self.experiment = experiment
        self.metrics = {}
        self.trace = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enzyme": self.enzyme,
            "method": self.method,
            "experiment": self.experiment,
            **self.metrics
        }

    def to_csv_row(self) -> str:
        row = f"{self.enzyme},{self.method},{self.experiment}"
        for key in ["faithfulness", "hallucination_rate", "evidence_utilization", "trace_completeness", "grounding_score"]:
            row += f",{self.metrics.get(key, 0.0):.4f}"
        return row

class AblationStudy:
    def __init__(self):
        self.results = []

    def add_result(self, removed_component: str, grounding_score: float, metrics: Dict[str, float]):
        self.results.append({
            "removed_component": removed_component,
            "grounding_score": grounding_score,
            **metrics
        })

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return self.results

    def get_degradation(self, baseline_score: float) -> List[Dict[str, Any]]:
        return [
            {
                "removed_component": r["removed_component"],
                "grounding_score": r["grounding_score"],
                "degradation": baseline_score - r["grounding_score"],
                "degradation_percent": ((baseline_score - r["grounding_score"]) / baseline_score * 100) if baseline_score > 0 else 0
            }
            for r in self.results
        ]
