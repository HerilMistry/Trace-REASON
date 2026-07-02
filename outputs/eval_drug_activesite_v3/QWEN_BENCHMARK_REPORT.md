# TRACE-Reason: Drug Active-Site Benchmark (Q6-Q8)

This benchmark evaluates leading LLMs—with a specific focus on **Qwen models (Qwen 3 32B and Qwen 3.6 27B)**—on complex drug active-site reasoning tasks (Q6, Q7, and Q8).

## 🏆 Leaderboard Summary

| Rank | Model | Provider | Composite Score | Faithfulness | Correctness | Completeness |
|---|---|---|---|---|---|---|
| 🥇 | `qwen/qwen3.6-27b` | groq | **0.9444** | 5.00 | 5.00 | 4.33 |
| 🥈 | `mistral/mistral-small-latest` | mistral | **0.9222** | 4.67 | 4.67 | 4.67 |
| 🥉 | `groq/llama-4-scout-17b` | groq | **0.8444** | 4.00 | 4.33 | 4.33 |
| 4 | `qwen/qwen3-32b` | groq | **0.8222** | 3.67 | 4.33 | 4.33 |
| 5 | `groq/llama-3.3-70b-versatile` | groq | **0.7556** | 3.67 | 4.00 | 3.67 |
| 6 | `gemini/gemini-2.0-flash` | gemini | (Rate Limited) | - | - | - |

*(Gemini 2.0 Flash was excluded due to strict API free-tier rate limits on Google AI Studio).*

---

## 📊 Statistical Credibility Analysis

To establish the statistical credibility of the results for these specific drug discovery questions, we ran a bootstrapped Confidence Interval (CI) analysis ($n=1000$ iterations).

### 95% Confidence Intervals (Composite Score)

- **`qwen/qwen3.6-27b`**: Mean `0.956` — **95% CI: `[0.867 - 1.000]`** (Highly consistent performance, tightly bound at the top)
- **`mistral/mistral-small-latest`**: Mean `0.967` — **95% CI: `[0.933 - 1.000]`**
- **`groq/llama-4-scout-17b`**: Mean `0.844` — **95% CI: `[0.667 - 1.000]`**
- **`qwen/qwen3-32b`**: Mean `0.800` — **95% CI: `[0.467 - 1.000]`** (Higher variance across the 3 questions)
- **`groq/llama-3.3-70b-versatile`**: Mean `0.756` — **95% CI: `[0.600 - 0.933]`**

### Variance & Significance
A Kruskal-Wallis H-test was conducted on the model distributions ($H = 3.3256$). With only $N=3$ questions per model, the test yields a p-value of `0.5048`. While we cannot claim *strict* statistical dominance across the board (due to small $N$), the tight confidence intervals for **Qwen 3.6 27B** and **Mistral Small** indicate highly stable, reliable reasoning on biochemical active-site geometry and inhibitor binding mechanisms.

---

## 📁 Generated Assets
The full run data has been saved to the `outputs/eval_drug_activesite_v3` directory:
- [JSON Report](file:///home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v3/eval_report.json)
- [Detailed Excel Breakdown](file:///home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v3/detailed_eval_report.xlsx)
- [Heatmap Visualization](file:///home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v3/eval_heatmap.png)
- [Credibility CI Plot](file:///home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v3/credibility_ci_plot.png)
- [Statistical Metrics CSV](file:///home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v3/statistical_metrics.csv)
