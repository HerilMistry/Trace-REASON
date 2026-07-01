# TRACE-Reason Multi-Model Evaluation Report

**Generated:** 2026-06-24 18:55:08  
**Enzyme:** LRRK2  
**Mutation:** G2019S  
**Mode:** direct  
**Models evaluated:** 7  
**Questions:** 5

---

## 🏆 Overall Leaderboard

> Composite = (Faithfulness + Correctness + Completeness) / 3 × (1 − Hallucination Rate)
> Scores normalised to [0, 1]. Higher is better. Hallucination Rate: lower is better.

| Rank   | Model                   | Provider   |   Composite↓ |   Faith. |   Correct. |   Complete. |   Halluc.↓ |   Latency(s) |   Tokens | Success   |
|--------|-------------------------|------------|--------------|----------|------------|-------------|------------|--------------|----------|-----------|
| 🥇     | qwen3-32b               | groq       |       0.9333 |      4.6 |        4.8 |         4.8 |      0     |         17.5 |     1469 | 5/5       |
| 🥈     | open-mistral-7b         | mistral    |       0.9    |      4.2 |        4.8 |         4.8 |      0     |         12.9 |     1254 | 5/5       |
| 🥉     | llama-3.3-70b-versatile | groq       |       0.8735 |      4.2 |        4.4 |         5   |      0.012 |          2.3 |      659 | 5/5       |
| #4     | llama-4-scout-17b       | groq       |       0.85   |      4.2 |        4.6 |         4.4 |      0     |          2.8 |      625 | 5/5       |
| #5     | mistral-small-latest    | mistral    |       0.7834 |      3.6 |        4.4 |         4.4 |      0     |          6.5 |     1017 | 5/5       |
| #6     | llama-3.1-8b-instant    | groq       |       0.703  |      3.8 |        3.8 |         4   |      0.018 |          8.8 |      589 | 5/5       |
| #7     | gemini-1.5-flash        | gemini     |       0      |      0   |        0   |         0   |      0     |          0.4 |        0 | 0/5       |

---

## 📊 Per-Question Breakdown

| Q   | Model                   |   Composite |   Faith. |   Correct. |   Complete. |   Halluc. |   Latency(s) |
|-----|-------------------------|-------------|----------|------------|-------------|-----------|--------------|
| Q1  | llama-3.3-70b-versatile |      1      |        5 |          5 |           5 |     0     |          2   |
| Q1  | llama-4-scout-17b       |      1      |        5 |          5 |           5 |     0     |          3.6 |
| Q1  | qwen3-32b               |      1      |        5 |          5 |           5 |     0     |          3.4 |
| Q1  | open-mistral-7b         |      1      |        5 |          5 |           5 |     0     |         12.3 |
| Q1  | mistral-small-latest    |      0.9167 |        4 |          5 |           5 |     0     |          6.6 |
| Q1  | llama-3.1-8b-instant    |      0.8333 |        4 |          4 |           5 |     0     |          0.9 |
| Q1  | gemini-1.5-flash        |      0      |        1 |          1 |           1 |     0     |          0.5 |
| Q2  | llama-4-scout-17b       |      1      |        5 |          5 |           5 |     0     |          2.7 |
| Q2  | qwen3-32b               |      1      |        5 |          5 |           5 |     0     |          8.6 |
| Q2  | llama-3.3-70b-versatile |      0.7843 |        4 |          4 |           5 |     0.059 |          2.7 |
| Q2  | llama-3.1-8b-instant    |      0.6818 |        4 |          4 |           4 |     0.091 |          1.6 |
| Q2  | mistral-small-latest    |      0.6667 |        3 |          4 |           4 |     0     |          8.5 |
| Q2  | open-mistral-7b         |      0.6667 |        3 |          4 |           4 |     0     |         15.6 |
| Q2  | gemini-1.5-flash        |      0      |        1 |          1 |           1 |     0     |          0.4 |
| Q3  | mistral-small-latest    |      0.9167 |        4 |          5 |           5 |     0     |          5.8 |
| Q3  | open-mistral-7b         |      0.9167 |        4 |          5 |           5 |     0     |         14.5 |
| Q3  | llama-3.3-70b-versatile |      0.8333 |        4 |          4 |           5 |     0     |          2   |
| Q3  | qwen3-32b               |      0.6667 |        3 |          4 |           4 |     0     |         22.7 |
| Q3  | llama-4-scout-17b       |      0.5833 |        3 |          4 |           3 |     0     |          2.1 |
| Q3  | llama-3.1-8b-instant    |      0.5    |        3 |          3 |           3 |     0     |         29.3 |
| Q3  | gemini-1.5-flash        |      0      |        1 |          1 |           1 |     0     |          0.4 |
| Q4  | qwen3-32b               |      1      |        5 |          5 |           5 |     0     |         24.3 |
| Q4  | open-mistral-7b         |      1      |        5 |          5 |           5 |     0     |         10.7 |
| Q4  | llama-3.3-70b-versatile |      0.8333 |        4 |          4 |           5 |     0     |          2.4 |
| Q4  | llama-4-scout-17b       |      0.75   |        4 |          4 |           4 |     0     |          2   |
| Q4  | llama-3.1-8b-instant    |      0.5833 |        3 |          3 |           4 |     0     |          1.1 |
| Q4  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| Q4  | gemini-1.5-flash        |      0      |        1 |          1 |           1 |     0     |          0.5 |
| Q5  | qwen3-32b               |      1      |        5 |          5 |           5 |     0     |         28.5 |
| Q5  | llama-3.3-70b-versatile |      0.9167 |        4 |          5 |           5 |     0     |          2.2 |
| Q5  | llama-3.1-8b-instant    |      0.9167 |        5 |          5 |           4 |     0     |         11.3 |
| Q5  | llama-4-scout-17b       |      0.9167 |        4 |          5 |           5 |     0     |          3.5 |
| Q5  | mistral-small-latest    |      0.9167 |        4 |          5 |           5 |     0     |          6.2 |
| Q5  | open-mistral-7b         |      0.9167 |        4 |          5 |           5 |     0     |         11.3 |
| Q5  | gemini-1.5-flash        |      0      |        1 |          1 |           1 |     0     |          0.4 |

---

## 🔥 Heatmap: Model × Metric

![TRACE-Reason Evaluation Heatmap](/home/heril/Trace/Trace-REASON/outputs/eval/eval_heatmap.png)

---

## 📝 Key Findings

- **Best overall model:** groq/qwen3-32b (composite = 0.9333)
- **Lowest hallucination rate:** groq/qwen3-32b (0.000)
- **Fastest model:** gemini/gemini-1.5-flash (0.4s avg)
- **Most faithful:** groq/qwen3-32b (4.60/5)

---

## ℹ️ Methodology

- **Backbone temperature:** 0.0 (deterministic, reproducible)
- **Judge temperature:** 0.0
- **Judge rotation:** Each model is scored by a judge from a different provider
- **Hallucination rate:** atomic claims extracted via sentence splitting; unsupported claims = those not grounded in the evidence package
- **Composite formula:** `(F + C₁ + C₂) / 3 × (1 − H)` where F=Faithfulness, C₁=Correctness, C₂=Completeness, H=Hallucination rate
