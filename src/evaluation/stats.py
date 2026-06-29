import pandas as pd
import numpy as np
from scipy import stats
import os

class StatisticalAnalyzer:
    def __init__(self, baseline_csv, trace_csv):
        self.baseline_csv = baseline_csv
        self.trace_csv = trace_csv
        self.reports_dir = "outputs/reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def run_analysis(self):
        if not os.path.exists(self.baseline_csv) or not os.path.exists(self.trace_csv):
            print("CSV files not found for statistical analysis.")
            return

        baseline_df = pd.read_csv(self.baseline_csv)
        trace_df = pd.read_csv(self.trace_csv)

        metrics = ["faithfulness", "hallucination_rate", "evidence_utilization", "trace_completeness", "grounding_score"]
        
        report_lines = ["# Statistical Analysis Report\n"]
        
        for metric in metrics:
            if metric not in baseline_df.columns or metric not in trace_df.columns:
                continue

            base_vals = baseline_df[metric]
            trace_vals = trace_df[metric]

            base_mean, base_std = base_vals.mean(), base_vals.std()
            trace_mean, trace_std = trace_vals.mean(), trace_vals.std()

            base_ci = 1.96 * base_std / np.sqrt(len(base_vals)) if len(base_vals) > 0 else 0
            trace_ci = 1.96 * trace_std / np.sqrt(len(trace_vals)) if len(trace_vals) > 0 else 0

            # Paired t-test
            min_len = min(len(base_vals), len(trace_vals))
            t_stat, p_val = stats.ttest_rel(base_vals[:min_len], trace_vals[:min_len])

            report_lines.append(f"## Metric: {metric}")
            report_lines.append(f"- **Baseline**: {base_mean:.4f} ± {base_std:.4f} (95% CI: [{base_mean-base_ci:.4f}, {base_mean+base_ci:.4f}])")
            report_lines.append(f"- **TRACE-Reason**: {trace_mean:.4f} ± {trace_std:.4f} (95% CI: [{trace_mean-trace_ci:.4f}, {trace_mean+trace_ci:.4f}])")
            report_lines.append(f"- **Paired t-test**: t={t_stat:.4f}, p={p_val:.4e}")
            
            sig = "Yes" if p_val < 0.05 else "No"
            report_lines.append(f"- **Statistically Significant (p < 0.05)**: {sig}")
            report_lines.append("")

        report_path = os.path.join(self.reports_dir, "statistical_analysis.md")
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
        
        print(f"Statistical analysis saved to {report_path}")
