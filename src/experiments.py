import json
import os
import mlflow
from src.config import DATA_DIR, EXPERIMENTS_DIR
from src.ingestion import EnzymeDataset, DataIngestion
from src.embeddings import ESMEncoder, MutationGenerator
from src.evidence import EvidenceConstructor
from src.reasoning import ReasoningPipeline
from src.llm import LLMFactory
from src.evaluation import EvaluationMetrics, EvaluationResult
from src.evaluation.claims import ClaimEvaluator
from src.evaluation.judge import LLMJudge

class BaselineExperiment:
    def __init__(self):
        self.dataset = EnzymeDataset()
        self.ingestion = DataIngestion(self.dataset)
        self.llm = LLMFactory.create_provider("groq")
        self.results = []
        self.claim_evaluator = ClaimEvaluator()

    def run_baseline_query(self, enzyme_name: str) -> dict:
        details = self.ingestion.get_enzyme_details(enzyme_name)
        metadata = details.get("metadata", {})
        
        if not metadata:
            return {"error": f"Enzyme {enzyme_name} not found"}

        prompt = f"""
        Based ONLY on enzyme metadata, provide a brief explanation of enzyme function and disease association.
        
        Enzyme: {metadata.get('enzyme_name')}
        Gene Symbol: {metadata.get('gene_symbol')}
        EC Number: {metadata.get('ec_number')}
        UniProt: {metadata.get('uniprot_id')}
        Disease: {details.get('disease_indication')}
        
        Provide a 2-3 sentence explanation of:
        1. What this enzyme does
        2. How it relates to the disease
        
        Respond with JSON: {{
            "explanation": "",
            "confidence": 0.0
        }}
        """
        response = self.llm.structured_query(prompt, {
            "explanation": "string",
            "confidence": "number"
        })

        return response

    def run(self, enzyme_names: list = None):
        if enzyme_names is None:
            benchmark = self.dataset.get_benchmark_enzymes()
            enzyme_names = [e.get("gene_symbol") for e in benchmark]

        for enzyme in enzyme_names:
            llm_name = "groq"
            print(f"Running baseline: {enzyme} with {llm_name}")
            with mlflow.start_run(run_name=f"baseline_{enzyme}_{llm_name}", nested=True):
                mlflow.log_param("method", "baseline")
                mlflow.log_param("enzyme", enzyme)
                mlflow.log_param("model", llm_name)
                
                try:
                    response = self.run_baseline_query(enzyme)
                    explanation = response.get("explanation", "")
                        
                        # Use empty evidence package for baseline verification?
                        # Or use the actual constructed evidence package just for evaluation
                        encoder = ESMEncoder()
                        mut_gen = MutationGenerator(encoder)
                        evidence = EvidenceConstructor(self.ingestion, encoder, mut_gen).construct(enzyme)
                        
                        claim_res = self.claim_evaluator.evaluate_explanation(explanation, evidence, f"baseline_{enzyme}_{llm_name}")
                        
                        result = EvaluationResult(enzyme, "baseline", f"baseline_{llm_name}")
                        result.metrics = {
                            "faithfulness": claim_res["faithfulness"],
                            "hallucination_rate": claim_res["hallucination_rate"],
                            "evidence_utilization": 0.0,
                            "trace_completeness": 0.0,
                            "grounding_score": (0.4 * claim_res["faithfulness"]) - (0.3 * claim_res["hallucination_rate"])
                        }
                        result.trace = response
                        self.results.append(result)
                        
                        mlflow.log_metrics(result.metrics)
                        
                    except Exception as e:
                        print(f"Error processing {enzyme}: {e}")

    def save_results(self):
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
        csv_path = os.path.join(EXPERIMENTS_DIR, "baseline_results.csv")
        
        with open(csv_path, "w") as f:
            f.write("enzyme,method,experiment,faithfulness,hallucination_rate,evidence_utilization,trace_completeness,grounding_score\n")
            for result in self.results:
                f.write(result.to_csv_row() + "\n")
        
        print(f"Baseline results saved to {csv_path}")


class TraceReasonExperiment:
    def __init__(self):
        self.dataset = EnzymeDataset()
        self.ingestion = DataIngestion(self.dataset)
        self.embedding_encoder = ESMEncoder()
        self.mutation_gen = MutationGenerator(self.embedding_encoder)
        self.evidence_constructor = EvidenceConstructor(
            self.ingestion,
            self.embedding_encoder,
            self.mutation_gen
        )
        self.llm = LLMFactory.create_provider("groq")
        self.results = []
        self.claim_evaluator = ClaimEvaluator()
        self.judge = LLMJudge()

    def run_trace_reasoning(self, enzyme_name: str):
        print(f"Constructing evidence package for {enzyme_name}")
        evidence = self.evidence_constructor.construct(enzyme_name)

        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        trace.save_trace(f"{enzyme_name}_groq")

        explanation = trace.final_explanation
        claim_eval = self.claim_evaluator.evaluate_explanation(explanation, evidence, f"trace_reason_{enzyme_name}_groq")
        
        # LLM Judge Evaluation
        judge_scores = self.judge.evaluate(enzyme_name, "groq", "groq", explanation, evidence.get_summary())
        
        metrics = EvaluationMetrics.compute_all_metrics(trace, claim_eval)

        result = EvaluationResult(enzyme_name, "trace_reason", f"trace_reason_groq")
        result.metrics = metrics
        result.metrics.update(judge_scores)
        result.trace = trace

        return result

    def run(self, enzyme_names: list = None):
        if enzyme_names is None:
            benchmark = self.dataset.get_benchmark_enzymes()
            enzyme_names = [e.get("gene_symbol") for e in benchmark]

        for enzyme in enzyme_names:
            llm_name = "groq"
            print(f"Running TRACE-Reason: {enzyme} with {llm_name}")
            with mlflow.start_run(run_name=f"trace_{enzyme}_{llm_name}", nested=True):
                mlflow.log_param("method", "trace_reason")
                mlflow.log_param("enzyme", enzyme)
                mlflow.log_param("model", llm_name)
                try:
                    result = self.run_trace_reasoning(enzyme)
                    self.results.append(result)
                    mlflow.log_metrics(result.metrics)
                except Exception as e:
                    print(f"Error processing {enzyme} with TRACE-Reason: {e}")

    def save_results(self):
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
        csv_path = os.path.join(EXPERIMENTS_DIR, "trace_reason_results.csv")
        
        with open(csv_path, "w") as f:
            f.write("enzyme,method,experiment,faithfulness,hallucination_rate,evidence_utilization,trace_completeness,grounding_score\n")
            for result in self.results:
                f.write(result.to_csv_row() + "\n")
        
        print(f"TRACE-Reason results saved to {csv_path}")

class MutationBenchmarkExperiment:
    def __init__(self):
        self.dataset = EnzymeDataset()
        self.ingestion = DataIngestion(self.dataset)
        self.embedding_encoder = ESMEncoder()
        self.mutation_gen = MutationGenerator(self.embedding_encoder)
        self.evidence_constructor = EvidenceConstructor(
            self.ingestion,
            self.embedding_encoder,
            self.mutation_gen
        )
        self.llm = LLMFactory.create_provider("claude")
        self.results = []
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)

    def run(self, enzyme_names: list = None):
        if enzyme_names is None:
            benchmark = self.dataset.get_benchmark_enzymes()
            enzyme_names = [e.get("gene_symbol") for e in benchmark]

        for enzyme in enzyme_names:
            print(f"Running Mutation Benchmark: {enzyme}")
            
            # Wildtype
            evidence_wt = self.evidence_constructor.construct(enzyme)
            evidence_wt.mutation_evidence = [] # Exclude mutations to act as wildtype
            pipeline_wt = ReasoningPipeline(self.llm)
            trace_wt = pipeline_wt.execute(evidence_wt)
            
            # For each mutant
            conditions = ["wildtype", "benign", "moderate", "pathogenic"]
            for condition in conditions:
                with mlflow.start_run(run_name=f"mutation_{enzyme}_{condition}", nested=True):
                    mlflow.log_param("method", "mutation_benchmark")
                    mlflow.log_param("enzyme", enzyme)
                    mlflow.log_param("condition", condition)
                    
                    evidence_mut = self.evidence_constructor.construct(enzyme)
                    
                    if condition != "wildtype":
                        # Filter to only this mutation type
                        mut_type_map = {"pathogenic": "disruptive", "benign": "benign", "moderate": "moderate"}
                        evidence_mut.mutation_evidence = [m for m in evidence_mut.mutation_evidence if m.mutation_type == mut_type_map[condition]]
                    else:
                        evidence_mut.mutation_evidence = []
                        
                    pipeline_mut = ReasoningPipeline(self.llm)
                    trace_mut = pipeline_mut.execute(evidence_mut)
                    metrics = EvaluationMetrics.compute_all_metrics(trace_mut)
                    
                    self.results.append({
                        "enzyme": enzyme,
                        "condition": condition,
                        "grounding_score": metrics.get("grounding_score", 0.0)
                    })
                    mlflow.log_metric("grounding_score", metrics.get("grounding_score", 0.0))

    def save_results(self):
        csv_path = os.path.join(EXPERIMENTS_DIR, "mutation_sensitivity.csv")
        with open(csv_path, "w") as f:
            f.write("enzyme,condition,grounding_score\n")
            for r in self.results:
                f.write(f"{r['enzyme']},{r['condition']},{r['grounding_score']:.4f}\n")
        print(f"Mutation Sensitivity results saved to {csv_path}")
