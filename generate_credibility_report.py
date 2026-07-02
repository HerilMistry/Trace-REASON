import json
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

def compute_bootstrap_ci(data, num_bootstraps=1000, ci=95):
    """Compute bootstrapped confidence intervals for a mean."""
    if len(data) == 0:
        return 0, 0
    bootstrapped_means = []
    for _ in range(num_bootstraps):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrapped_means.append(np.mean(sample))
    lower = np.percentile(bootstrapped_means, (100 - ci) / 2)
    upper = np.percentile(bootstrapped_means, 100 - (100 - ci) / 2)
    return lower, upper

def main():
    input_file = "outputs/eval_drug_activesite_v3/eval_report.json"
    output_dir = "outputs/eval_drug_activesite_v3"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        data = json.load(f)
        
    raw_evals = data.get('raw_eval_records', [])
    judge_results = data.get('raw_judge_results', [])
    
    # Map judge results to composite score per eval
    # Composite score = (faithfulness + correctness + completeness) / 15
    eval_scores = []
    
    # We need to link judge results to the raw evals. 
    # Usually, we match by model_name and question_id
    for ev in raw_evals:
        if not ev.get('success'):
            continue
            
        model = ev['model_name']
        qid = ev['question_id']
        
        # Find matching judge result
        matching_judge = next((j for j in judge_results if j['backbone_model'] == model and j['question_id'] == qid), None)
        
        if matching_judge and not matching_judge.get('judge_error'):
            f = matching_judge.get('faithfulness', 0)
            c = matching_judge.get('correctness', 0)
            p = matching_judge.get('completeness', 0)
            composite = (f + c + p) / 15.0
            
            eval_scores.append({
                'Model': model,
                'Question': qid,
                'CompositeScore': composite,
                'Faithfulness': f,
                'Correctness': c,
                'Completeness': p
            })
            
    df = pd.DataFrame(eval_scores)
    
    if df.empty:
        print("No valid scores found.")
        return
        
    models = df['Model'].unique()
    
    print("\n" + "="*60)
    print("🔬 STATISTICAL CREDIBILITY REPORT (Q6, Q7, Q8)")
    print("="*60)
    
    # 1. 95% Confidence Intervals
    print("\n1. 95% Confidence Intervals (Bootstrapped, n=1000)")
    ci_data = []
    for m in models:
        scores = df[df['Model'] == m]['CompositeScore'].values
        mean_score = np.mean(scores)
        lower, upper = compute_bootstrap_ci(scores)
        ci_data.append({
            'Model': m,
            'Mean Score': mean_score,
            '95% CI Lower': lower,
            '95% CI Upper': upper
        })
        print(f"  - {m:35s}: {mean_score:.3f}  [{lower:.3f} - {upper:.3f}]")
        
    ci_df = pd.DataFrame(ci_data).sort_values(by='Mean Score', ascending=False)
    
    # 2. Statistical Significance (Kruskal-Wallis H-test)
    print("\n2. Statistical Significance Analysis")
    model_groups = [df[df['Model'] == m]['CompositeScore'].values for m in models]
    
    if len(model_groups) > 1:
        try:
            h_stat, p_val = stats.kruskal(*model_groups)
            print(f"  - Kruskal-Wallis H-test for overall model variance:")
            print(f"    H-statistic: {h_stat:.4f}")
            print(f"    p-value:     {p_val:.4e}")
            if p_val < 0.05:
                print("    Result: Significant differences exist between model performances (p < 0.05).")
            else:
                print("    Result: No statistically significant differences detected at alpha=0.05.")
        except Exception as e:
            print("  - Could not compute Kruskal-Wallis test.")
            
    # 3. Create Visualization
    plt.figure(figsize=(10, 6))
    
    # Error bar plot
    y_pos = np.arange(len(ci_df))
    means = ci_df['Mean Score'].values
    errors_lower = means - ci_df['95% CI Lower'].values
    errors_upper = ci_df['95% CI Upper'].values - means
    
    plt.barh(y_pos, means, xerr=[errors_lower, errors_upper], align='center', alpha=0.8, color='steelblue', capsize=5)
    plt.yticks(y_pos, ci_df['Model'].values)
    plt.xlabel('Composite Score (mean ± 95% CI)')
    plt.title('Model Performance with 95% Confidence Intervals (Q6, Q7, Q8)')
    plt.xlim(0, 1.05)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    viz_path = os.path.join(output_dir, "credibility_ci_plot.png")
    plt.savefig(viz_path, dpi=200)
    print(f"\n✓ Generated Confidence Interval plot: {viz_path}")
    
    # 4. Save detailed metrics to CSV
    csv_path = os.path.join(output_dir, "statistical_metrics.csv")
    ci_df.to_csv(csv_path, index=False)
    print(f"✓ Generated Statistical Metrics CSV: {csv_path}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
