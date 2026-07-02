# TRACE-Reason Multi-Model Evaluation Report

**Generated:** 2026-07-02 19:08:37  
**Enzyme:** LRRK2  
**Mutation:** G2019S  
**Mode:** direct  
**Models evaluated:** 6  
**Questions:** 3

---

## 🏆 Overall Leaderboard

> Composite = (Faithfulness + Correctness + Completeness) / 3 × (1 − Hallucination Rate)
> Scores normalised to [0, 1]. Higher is better. Hallucination Rate: lower is better.

| Rank   | Model                   | Provider   |   Composite↓ |   Faith. |   Correct. |   Complete. |   Halluc.↓ |   Latency(s) |   Tokens | Success   |
|--------|-------------------------|------------|--------------|----------|------------|-------------|------------|--------------|----------|-----------|
| 🥇     | qwen3.6-27b             | qwen       |       0.9444 |     5    |       5    |        4.33 |          0 |         11.4 |     2048 | 3/3       |
| 🥈     | llama-4-scout-17b       | groq       |       0.8055 |     4    |       4.33 |        4.33 |          0 |          2   |      616 | 3/3       |
| 🥉     | qwen3-32b               | qwen       |       0.75   |     3.67 |       4.33 |        4    |          0 |         13.4 |     1550 | 3/3       |
| #4     | llama-3.3-70b-versatile | groq       |       0.6945 |     3.67 |       4.33 |        3.33 |          0 |          2.9 |      662 | 3/3       |
| #5     | mistral-small-latest    | mistral    |       0.6389 |     3.33 |       3.67 |        3.67 |          0 |          9.3 |     1350 | 3/3       |
| #6     | gemini-2.0-flash        | gemini     |       0      |     0    |       0    |        0    |          0 |          0.4 |        0 | 0/3       |

---

## 📊 Per-Question Breakdown

| Q   | Model                   |   Composite |   Faith. |   Correct. |   Complete. |   Halluc. |   Latency(s) |
|-----|-------------------------|-------------|----------|------------|-------------|-----------|--------------|
| Q6  | llama-4-scout-17b       |      1      |        5 |          5 |           5 |         0 |          1.8 |
| Q6  | qwen3.6-27b             |      1      |        5 |          5 |           5 |         0 |          4.4 |
| Q6  | mistral-small-latest    |      1      |        5 |          5 |           5 |         0 |          8.4 |
| Q6  | qwen3-32b               |      0.9167 |        4 |          5 |           5 |         0 |          3.5 |
| Q6  | llama-3.3-70b-versatile |      0.6667 |        4 |          4 |           3 |         0 |          2.3 |
| Q6  | gemini-2.0-flash        |      0      |        1 |          1 |           1 |         0 |          0.4 |
| Q7  | qwen3-32b               |      1      |        5 |          5 |           5 |         0 |         11.1 |
| Q7  | qwen3.6-27b             |      1      |        5 |          5 |           5 |         0 |          4.3 |
| Q7  | llama-3.3-70b-versatile |      0.9167 |        4 |          5 |           5 |         0 |          4   |
| Q7  | mistral-small-latest    |      0.9167 |        4 |          5 |           5 |         0 |          7.4 |
| Q7  | llama-4-scout-17b       |      0.8333 |        4 |          4 |           5 |         0 |          1.9 |
| Q7  | gemini-2.0-flash        |      0      |        1 |          1 |           1 |         0 |          0.4 |
| Q8  | qwen3.6-27b             |      0.8333 |        5 |          5 |           3 |         0 |         25.5 |
| Q8  | llama-4-scout-17b       |      0.5833 |        3 |          4 |           3 |         0 |          2.3 |
| Q8  | llama-3.3-70b-versatile |      0.5    |        3 |          4 |           2 |         0 |          2.4 |
| Q8  | qwen3-32b               |      0.3333 |        2 |          3 |           2 |         0 |         25.7 |
| Q8  | gemini-2.0-flash        |      0      |        1 |          1 |           1 |         0 |          0.4 |
| Q8  | mistral-small-latest    |      0      |        1 |          1 |           1 |         0 |         12.2 |

---

## 🔥 Heatmap: Model × Metric

![TRACE-Reason Evaluation Heatmap](/home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v3/eval_heatmap.png)

---

## 📝 Key Findings

- **Best overall model:** qwen/qwen3.6-27b (composite = 0.9444)
- **Lowest hallucination rate:** qwen/qwen3.6-27b (0.000)
- **Fastest model:** gemini/gemini-2.0-flash (0.4s avg)
- **Most faithful:** qwen/qwen3.6-27b (5.00/5)

---

## ℹ️ Methodology

- **Backbone temperature:** 0.0 (deterministic, reproducible)
- **Judge temperature:** 0.0
- **Judge rotation:** Each model is scored by a judge from a different provider
- **Hallucination rate:** atomic claims extracted via sentence splitting; unsupported claims = those not grounded in the evidence package
- **Composite formula:** `(F + C₁ + C₂) / 3 × (1 − H)` where F=Faithfulness, C₁=Correctness, C₂=Completeness, H=Hallucination rate
