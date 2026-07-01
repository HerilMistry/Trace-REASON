# TRACE-Reason Multi-Model Evaluation Report

**Generated:** 2026-06-30 00:20:36  
**Enzyme:** LRRK2  
**Mutation:** G2019S  
**Mode:** direct  
**Models evaluated:** 4  
**Questions:** 3

---

## 🏆 Overall Leaderboard

> Composite = (Faithfulness + Correctness + Completeness) / 3 × (1 − Hallucination Rate)
> Scores normalised to [0, 1]. Higher is better. Hallucination Rate: lower is better.

| Rank   | Model                   | Provider   |   Composite↓ |   Faith. |   Correct. |   Complete. |   Halluc.↓ |   Latency(s) |   Tokens | Success   |
|--------|-------------------------|------------|--------------|----------|------------|-------------|------------|--------------|----------|-----------|
| 🥇     | mistral-small-latest    | mistral    |       0.8333 |     4    |       4.67 |        4.33 |          0 |          9.2 |     1350 | 3/3       |
| 🥈     | llama-4-scout-17b       | groq       |       0.6944 |     3.67 |       3.67 |        4    |          0 |          1.9 |      673 | 3/3       |
| 🥉     | llama-3.3-70b-versatile | groq       |       0.6111 |     3    |       3.67 |        3.67 |          0 |          3   |      767 | 3/3       |
| #4     | gemini-2.0-flash        | gemini     |       0      |     0    |       0    |        0    |          0 |          0.4 |        0 | 0/3       |

---

## 📊 Per-Question Breakdown

| Q   | Model                   |   Composite |   Faith. |   Correct. |   Complete. |   Halluc. |   Latency(s) |
|-----|-------------------------|-------------|----------|------------|-------------|-----------|--------------|
| Q6  | mistral-small-latest    |      1      |        5 |          5 |           5 |         0 |          8.4 |
| Q6  | llama-4-scout-17b       |      0.8333 |        4 |          4 |           5 |         0 |          2.2 |
| Q6  | llama-3.3-70b-versatile |      0.6667 |        3 |          4 |           4 |         0 |          3.7 |
| Q6  | gemini-2.0-flash        |      0      |        1 |          1 |           1 |         0 |          0.4 |
| Q7  | mistral-small-latest    |      0.9167 |        4 |          5 |           5 |         0 |          7.2 |
| Q7  | llama-3.3-70b-versatile |      0.8333 |        4 |          4 |           5 |         0 |          2.5 |
| Q7  | llama-4-scout-17b       |      0.8333 |        4 |          4 |           5 |         0 |          1.8 |
| Q7  | gemini-2.0-flash        |      0      |        1 |          1 |           1 |         0 |          0.4 |
| Q8  | mistral-small-latest    |      0.5833 |        3 |          4 |           3 |         0 |         11.9 |
| Q8  | llama-4-scout-17b       |      0.4167 |        3 |          3 |           2 |         0 |          1.6 |
| Q8  | llama-3.3-70b-versatile |      0.3333 |        2 |          3 |           2 |         0 |          2.9 |
| Q8  | gemini-2.0-flash        |      0      |        1 |          1 |           1 |         0 |          0.4 |

---

## 🔥 Heatmap: Model × Metric

![TRACE-Reason Evaluation Heatmap](/home/heril/Trace/Trace-REASON/outputs/eval_drug_activesite_v2/eval_heatmap.png)

---

## 📝 Key Findings

- **Best overall model:** mistral/mistral-small-latest (composite = 0.8333)
- **Lowest hallucination rate:** mistral/mistral-small-latest (0.000)
- **Fastest model:** gemini/gemini-2.0-flash (0.4s avg)
- **Most faithful:** mistral/mistral-small-latest (4.00/5)

---

## ℹ️ Methodology

- **Backbone temperature:** 0.0 (deterministic, reproducible)
- **Judge temperature:** 0.0
- **Judge rotation:** Each model is scored by a judge from a different provider
- **Hallucination rate:** atomic claims extracted via sentence splitting; unsupported claims = those not grounded in the evidence package
- **Composite formula:** `(F + C₁ + C₂) / 3 × (1 − H)` where F=Faithfulness, C₁=Correctness, C₂=Completeness, H=Hallucination rate
