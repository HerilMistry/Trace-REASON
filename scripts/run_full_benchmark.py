import mlflow
import os

from src.config import EXPERIMENTS_DIR
from src.ingestion import EnzymeDataset
from src.experiments import BaselineExperiment, TraceReasonExperiment, MutationBenchmarkExperiment
from src.ablation import NodeAblationExperiment, MutationAblationExperiment
from src.evaluation.stats import StatisticalAnalyzer
from src.evaluation.figures import FigureGenerator
from src.evaluation.quality import DataQualityChecker
from src.evaluation.report import ReportGenerator

def main():
    print("Starting TRACE-Reason Full Benchmark Pipeline...")
    
    # 1. Dataset Quality Checks
    print("\n--- Running Dataset Quality Checks ---")
    dataset = EnzymeDataset()
    quality_checker = DataQualityChecker(dataset)
    quality_checker.run_checks()
    
    # Setup MLflow
    mlflow.set_experiment("TRACE-Reason Benchmark")
    
    with mlflow.start_run(run_name="Full_Benchmark_Suite"):
        mlflow.log_param("dataset_version", "1.0")
        mlflow.log_param("prompt_version", "1.0")
        
        # 2. Baseline Experiment
        print("\n--- Running Baseline Experiment ---")
        baseline_exp = BaselineExperiment()
        # For speed, just take a few enzymes if we want, but user wants all.
        baseline_exp.run()
        baseline_exp.save_results()
        
        # 3. TRACE-Reason Experiment
        print("\n--- Running TRACE-Reason Experiment ---")
        trace_exp = TraceReasonExperiment()
        trace_exp.run()
        trace_exp.save_results()
        
        # 4. Mutation Benchmark Experiment
        print("\n--- Running Mutation Benchmark ---")
        mutation_exp = MutationBenchmarkExperiment()
        mutation_exp.run()
        mutation_exp.save_results()
        
        # 5. Ablation Framework
        print("\n--- Running Node Ablation ---")
        node_ablation = NodeAblationExperiment()
        node_ablation.run()
        node_ablation.save_results()
        
        print("\n--- Running Mutation Ablation ---")
        mut_ablation = MutationAblationExperiment()
        mut_ablation.run()
        mut_ablation.save_results()
        
    # 6. Statistical Analysis
    print("\n--- Running Statistical Analysis ---")
    stats_analyzer = StatisticalAnalyzer(
        baseline_csv=os.path.join(EXPERIMENTS_DIR, "baseline_results.csv"),
        trace_csv=os.path.join(EXPERIMENTS_DIR, "trace_reason_results.csv")
    )
    stats_analyzer.run_analysis()
    
    # 7. Paper-Ready Figures
    print("\n--- Generating Paper-Ready Figures ---")
    fig_generator = FigureGenerator()
    fig_generator.generate_all_figures(
        baseline_csv=os.path.join(EXPERIMENTS_DIR, "baseline_results.csv"),
        trace_csv=os.path.join(EXPERIMENTS_DIR, "trace_reason_results.csv"),
        mutation_csv=os.path.join(EXPERIMENTS_DIR, "mutation_sensitivity.csv"),
        ablation_csv=os.path.join(EXPERIMENTS_DIR, "node_ablation.csv")
    )
    
    # 8. Research Report
    print("\n--- Generating Research Report ---")
    report_gen = ReportGenerator()
    report_gen.generate_final_report()
    
    print("\nBenchmark Pipeline Completed Successfully!")
    print("Check outputs/ folder for all results, traces, reports, and figures.")

if __name__ == "__main__":
    main()
