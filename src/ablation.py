import os
from src.config import DATA_DIR, EXPERIMENTS_DIR
from src.ingestion import EnzymeDataset, DataIngestion
from src.embeddings import ESMEncoder, MutationGenerator
from src.evidence import EvidenceConstructor
from src.reasoning import ReasoningPipeline
from src.llm import LLMFactory
from src.evaluation import EvaluationMetrics, EvaluationResult, AblationStudy

class MutationAblationExperiment:
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

    def run_with_mutations(self, enzyme_name: str):
        evidence = self.evidence_constructor.construct(enzyme_name)
        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        metrics = EvaluationMetrics.compute_all_metrics(trace)
        return metrics

    def run_without_mutations(self, enzyme_name: str):
        evidence = self.evidence_constructor.construct(enzyme_name)
        evidence.mutation_evidence = []
        evidence.mutation_embeddings = {}
        
        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        metrics = EvaluationMetrics.compute_all_metrics(trace)
        return metrics

    def run(self, enzyme_names: list = None):
        if enzyme_names is None:
            benchmark = self.dataset.get_benchmark_enzymes()
            enzyme_names = [e.get("gene_symbol") for e in benchmark]

        for enzyme in enzyme_names:
            print(f"Running mutation ablation: {enzyme}")
            
            try:
                metrics_with = self.run_with_mutations(enzyme)
                metrics_without = self.run_without_mutations(enzyme)
                
                self.results.append({
                    "enzyme": enzyme,
                    "condition": "with_mutations",
                    "grounding_score": metrics_with["grounding_score"],
                    **metrics_with
                })
                
                self.results.append({
                    "enzyme": enzyme,
                    "condition": "without_mutations",
                    "grounding_score": metrics_without["grounding_score"],
                    **metrics_without
                })
            except Exception as e:
                print(f"Error in mutation ablation for {enzyme}: {e}")

    def save_results(self):
        csv_path = os.path.join(EXPERIMENTS_DIR, "mutation_ablation.csv")
        
        with open(csv_path, "w") as f:
            f.write("enzyme,condition,grounding_score,faithfulness,hallucination_rate,evidence_utilization,trace_completeness\n")
            for result in self.results:
                row = f"{result['enzyme']},{result['condition']},{result['grounding_score']:.4f},{result['faithfulness']:.4f},{result['hallucination_rate']:.4f},{result['evidence_utilization']:.4f},{result['trace_completeness']:.4f}"
                f.write(row + "\n")
        
        print(f"Mutation ablation results saved to {csv_path}")

class NodeAblationExperiment:
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
        self.study = AblationStudy()

    def run_baseline_full_pipeline(self, enzyme_name: str):
        evidence = self.evidence_constructor.construct(enzyme_name)
        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        metrics = EvaluationMetrics.compute_all_metrics(trace)
        return metrics

    def run_without_mutation_node(self, enzyme_name: str):
        evidence = self.evidence_constructor.construct(enzyme_name)
        evidence.mutation_evidence = []
        
        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        metrics = EvaluationMetrics.compute_all_metrics(trace)
        return metrics

    def run_without_disease_node(self, enzyme_name: str):
        evidence = self.evidence_constructor.construct(enzyme_name)
        evidence.disease.indication = ""
        evidence.pathogenic_variants = []
        
        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        metrics = EvaluationMetrics.compute_all_metrics(trace)
        return metrics

    def run_without_kinetic_node(self, enzyme_name: str):
        evidence = self.evidence_constructor.construct(enzyme_name)
        evidence.kinetic_evidence = []
        
        pipeline = ReasoningPipeline(self.llm)
        trace = pipeline.execute(evidence)
        metrics = EvaluationMetrics.compute_all_metrics(trace)
        return metrics

    def run(self, enzyme_names: list = None):
        if enzyme_names is None:
            benchmark = self.dataset.get_benchmark_enzymes()
            enzyme_names = [e.get("gene_symbol") for e in benchmark]

        for enzyme in enzyme_names:
            print(f"Running node ablation: {enzyme}")
            
            try:
                baseline_metrics = self.run_baseline_full_pipeline(enzyme)
                baseline_score = baseline_metrics["grounding_score"]
                
                no_mutation = self.run_without_mutation_node(enzyme)
                self.study.add_result("Mutation Node", no_mutation["grounding_score"], no_mutation)
                
                no_disease = self.run_without_disease_node(enzyme)
                self.study.add_result("Disease Node", no_disease["grounding_score"], no_disease)
                
                no_kinetic = self.run_without_kinetic_node(enzyme)
                self.study.add_result("Kinetic Node", no_kinetic["grounding_score"], no_kinetic)
                
            except Exception as e:
                print(f"Error in node ablation for {enzyme}: {e}")

    def save_results(self):
        csv_path = os.path.join(EXPERIMENTS_DIR, "node_ablation.csv")
        degradations = self.study.get_degradation(0.6)
        
        with open(csv_path, "w") as f:
            f.write("removed_component,grounding_score,degradation,degradation_percent\n")
            for deg in degradations:
                row = f"{deg['removed_component']},{deg['grounding_score']:.4f},{deg['degradation']:.4f},{deg['degradation_percent']:.2f}"
                f.write(row + "\n")
        
        print(f"Node ablation results saved to {csv_path}")
