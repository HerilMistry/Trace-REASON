import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

class FigureGenerator:
    def __init__(self):
        self.figures_dir = "outputs/figures"
        os.makedirs(self.figures_dir, exist_ok=True)
        sns.set_theme(style="whitegrid")

    def _save_fig(self, name):
        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, f"{name}.png"), dpi=300)
        plt.savefig(os.path.join(self.figures_dir, f"{name}.pdf"))
        plt.close()

    def generate_comparison_bar(self, baseline_csv, trace_csv, metric, title, filename):
        if not os.path.exists(baseline_csv) or not os.path.exists(trace_csv):
            return
        
        base_df = pd.read_csv(baseline_csv)
        trace_df = pd.read_csv(trace_csv)

        base_df['System'] = 'Baseline'
        trace_df['System'] = 'TRACE-Reason'

        combined = pd.concat([base_df, trace_df])

        plt.figure(figsize=(10, 6))
        sns.barplot(data=combined, x='enzyme', y=metric, hue='System')
        plt.title(title)
        plt.xticks(rotation=45)
        self._save_fig(filename)

    def generate_all_figures(self, baseline_csv, trace_csv, mutation_csv, ablation_csv):
        # 1. Faithfulness Comparison
        self.generate_comparison_bar(baseline_csv, trace_csv, 'faithfulness', 'Faithfulness Comparison: Baseline vs TRACE', 'faithfulness_comparison')

        # 2. Hallucination Comparison
        self.generate_comparison_bar(baseline_csv, trace_csv, 'hallucination_rate', 'Hallucination Comparison: Baseline vs TRACE', 'hallucination_comparison')

        # 3. Grounding Score Comparison
        self.generate_comparison_bar(baseline_csv, trace_csv, 'grounding_score', 'Grounding Score Comparison: Baseline vs TRACE', 'grounding_score_comparison')

        # 4. Mutation Sensitivity
        if os.path.exists(mutation_csv):
            mut_df = pd.read_csv(mutation_csv)
            plt.figure(figsize=(10, 6))
            sns.barplot(data=mut_df, x='enzyme', y='grounding_score', hue='condition')
            plt.title('Mutation Sensitivity: Wildtype vs Mutants')
            plt.xticks(rotation=45)
            self._save_fig('mutation_sensitivity')

        # 5. Ablation Results
        if os.path.exists(ablation_csv):
            abl_df = pd.read_csv(ablation_csv)
            plt.figure(figsize=(8, 6))
            sns.barplot(data=abl_df, x='removed_component', y='degradation')
            plt.title('Ablation Results: Impact of Component Removal')
            plt.ylabel('Degradation in Grounding Score')
            plt.xticks(rotation=45)
            self._save_fig('ablation_results')
        
        print(f"Figures generated in {self.figures_dir}")
