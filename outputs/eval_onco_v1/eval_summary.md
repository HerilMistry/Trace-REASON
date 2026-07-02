# TRACE-Reason Multi-Model Evaluation Report

**Generated:** 2026-07-02 20:27:04  
**Enzyme:** LRRK2  
**Mutation:** G2019S  
**Mode:** direct  
**Models evaluated:** 5  
**Questions:** 56

---

## 🏆 Overall Leaderboard

> Composite = (Faithfulness + Correctness + Completeness) / 3 × (1 − Hallucination Rate)
> Scores normalised to [0, 1]. Higher is better. Hallucination Rate: lower is better.

| Rank   | Model                   | Provider   |   Composite↓ |   Faith. |   Correct. |   Complete. |   Halluc.↓ |   Latency(s) |   Tokens | Success   |
|--------|-------------------------|------------|--------------|----------|------------|-------------|------------|--------------|----------|-----------|
| 🥇     | llama-3.3-70b-versatile | groq       |       0.5    |        3 |          3 |           3 |      0     |          5.3 |      640 | 56/56     |
| 🥈     | qwen3-32b               | qwen       |       0.5    |        3 |          3 |           3 |      0     |         21.8 |     1753 | 55/56     |
| 🥉     | mistral-small-latest    | mistral    |       0.5    |        3 |          3 |           3 |      0     |          8   |     1188 | 56/56     |
| #4     | llama-4-scout-17b       | groq       |       0.4995 |        3 |          3 |           3 |      0.001 |          2.7 |      606 | 56/56     |
| #5     | qwen3.6-27b             | qwen       |       0.499  |        3 |          3 |           3 |      0.002 |         18.4 |     2048 | 56/56     |

---

## 📊 Per-Question Breakdown

| Q        | Model                   |   Composite |   Faith. |   Correct. |   Complete. |   Halluc. |   Latency(s) |
|----------|-------------------------|-------------|----------|------------|-------------|-----------|--------------|
| QAS-001  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          1.9 |
| QAS-001  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.8 |
| QAS-001  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |          3.8 |
| QAS-001  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |          4.4 |
| QAS-001  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.6 |
| QAS-004  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          1.8 |
| QAS-004  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.5 |
| QAS-004  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QAS-004  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         23.4 |
| QAS-004  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.7 |
| QAS-007  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          4.9 |
| QAS-007  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.8 |
| QAS-007  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         22.3 |
| QAS-007  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.4 |
| QAS-007  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.1 |
| QAS-010  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          4.2 |
| QAS-010  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          4.1 |
| QAS-010  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         22   |
| QAS-010  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QAS-010  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.3 |
| QAS-013  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          4   |
| QAS-013  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.9 |
| QAS-013  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         22.6 |
| QAS-013  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QAS-013  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6   |
| QAS-016  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.9 |
| QAS-016  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.1 |
| QAS-016  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         22   |
| QAS-016  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QAS-016  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.8 |
| QAS-019  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.3 |
| QAS-019  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.1 |
| QAS-019  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         18.8 |
| QAS-019  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.2 |
| QAS-019  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QAS-022  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.6 |
| QAS-022  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.4 |
| QAS-022  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         17.7 |
| QAS-022  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QAS-022  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.9 |
| QAS-025  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.5 |
| QAS-025  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.5 |
| QAS-025  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.6 |
| QAS-025  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QAS-025  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.1 |
| QAS-028  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.7 |
| QAS-028  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3   |
| QAS-028  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         22.9 |
| QAS-028  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QAS-028  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.2 |
| QAS-031  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.2 |
| QAS-031  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.9 |
| QAS-031  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         21.3 |
| QAS-031  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.2 |
| QAS-031  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.1 |
| QAS-034  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6   |
| QAS-034  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          4.4 |
| QAS-034  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.7 |
| QAS-034  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QAS-034  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.3 |
| QAS-037  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          4   |
| QAS-037  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          4.8 |
| QAS-037  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.6 |
| QAS-037  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.2 |
| QAS-037  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.2 |
| QAS-040  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.3 |
| QAS-040  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.6 |
| QAS-040  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         26.3 |
| QAS-040  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.2 |
| QAS-040  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         10.7 |
| QAS-042  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5   |
| QAS-042  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.2 |
| QAS-042  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         20.2 |
| QAS-042  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.3 |
| QAS-042  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.3 |
| QAS-045  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.4 |
| QAS-045  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.7 |
| QAS-045  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.7 |
| QAS-045  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.3 |
| QAS-045  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.9 |
| QAS-048  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QAS-048  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.3 |
| QAS-048  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         26   |
| QAS-048  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.2 |
| QAS-048  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.5 |
| QAS-051  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          8   |
| QAS-051  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2   |
| QAS-051  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.6 |
| QAS-051  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.3 |
| QAS-051  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.3 |
| QAS-054  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.5 |
| QAS-054  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.4 |
| QAS-054  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.7 |
| QAS-054  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QAS-054  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.5 |
| QDA-003  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          2.7 |
| QDA-003  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.9 |
| QDA-003  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         30   |
| QDA-003  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         10.4 |
| QDA-003  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         11   |
| QDA-006  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.8 |
| QDA-006  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.5 |
| QDA-006  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         26.4 |
| QDA-006  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QDA-006  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7   |
| QDA-009  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.6 |
| QDA-009  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.3 |
| QDA-009  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         24.6 |
| QDA-009  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QDA-009  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8   |
| QDA-012  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QDA-012  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.3 |
| QDA-012  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         31.3 |
| QDA-012  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QDA-012  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         10.3 |
| QDA-015  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          4.9 |
| QDA-015  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          5.2 |
| QDA-015  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         27.9 |
| QDA-015  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QDA-015  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.6 |
| QDA-018  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.5 |
| QDA-018  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.4 |
| QDA-018  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         21.2 |
| QDA-018  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QDA-018  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         10.5 |
| QDA-021  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.6 |
| QDA-021  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QDA-021  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         27   |
| QDA-021  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QDA-021  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          9.7 |
| QDA-024  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.7 |
| QDA-024  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.8 |
| QDA-024  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         25   |
| QDA-024  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.2 |
| QDA-024  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         10.5 |
| QDA-027  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.9 |
| QDA-027  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.7 |
| QDA-027  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.7 |
| QDA-027  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.2 |
| QDA-027  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.9 |
| QDA-030  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QDA-030  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.5 |
| QDA-030  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         18.9 |
| QDA-030  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.2 |
| QDA-030  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.4 |
| QDA-033  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.1 |
| QDA-033  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          6.2 |
| QDA-033  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         22.8 |
| QDA-033  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.1 |
| QDA-033  | qwen3.6-27b             |      0.4878 |        3 |          3 |           3 |     0.024 |         18.3 |
| QDA-036  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QDA-036  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.1 |
| QDA-036  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         24.8 |
| QDA-036  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.4 |
| QDA-036  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.3 |
| QDA-039  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.3 |
| QDA-039  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          4.1 |
| QDA-039  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.5 |
| QDA-039  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.2 |
| QDA-039  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         10   |
| QDA-041  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QDA-041  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.9 |
| QDA-041  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.2 |
| QDA-041  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QDA-041  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         11.9 |
| QDA-044  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.6 |
| QDA-044  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.7 |
| QDA-044  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         27   |
| QDA-044  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.2 |
| QDA-044  | qwen3.6-27b             |      0.4828 |        3 |          3 |           3 |     0.035 |         19.2 |
| QDA-047  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QDA-047  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.4 |
| QDA-047  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         26.2 |
| QDA-047  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.3 |
| QDA-047  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7   |
| QDA-050  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.3 |
| QDA-050  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.9 |
| QDA-050  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         25.4 |
| QDA-050  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.4 |
| QDA-050  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.3 |
| QDA-053  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.3 |
| QDA-053  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2   |
| QDA-053  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         25.1 |
| QDA-053  | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.4 |
| QDA-053  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         12.4 |
| QDA-056  | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.1 |
| QDA-056  | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.2 |
| QDA-056  | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.6 |
| QDA-056  | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.6 |
| QDA-056  | qwen3.6-27b             |      0.48   |        3 |          3 |           3 |     0.04  |         19.3 |
| QMoA-002 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          2.1 |
| QMoA-002 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.3 |
| QMoA-002 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |          8.9 |
| QMoA-002 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |          4.3 |
| QMoA-002 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.9 |
| QMoA-005 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          2.2 |
| QMoA-005 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |          3.9 |
| QMoA-005 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QMoA-005 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.6 |
| QMoA-005 | llama-4-scout-17b       |      0.4706 |        3 |          3 |           3 |     0.059 |          2.2 |
| QMoA-008 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.3 |
| QMoA-008 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.1 |
| QMoA-008 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         18.1 |
| QMoA-008 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         23.5 |
| QMoA-008 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.3 |
| QMoA-011 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.5 |
| QMoA-011 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.2 |
| QMoA-011 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         20.6 |
| QMoA-011 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QMoA-011 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.9 |
| QMoA-014 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5   |
| QMoA-014 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.5 |
| QMoA-014 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.5 |
| QMoA-014 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QMoA-014 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.2 |
| QMoA-017 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          3.1 |
| QMoA-017 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.8 |
| QMoA-017 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QMoA-017 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.6 |
| QMoA-017 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.6 |
| QMoA-020 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QMoA-020 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.3 |
| QMoA-020 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         18   |
| QMoA-020 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.6 |
| QMoA-020 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.3 |
| QMoA-023 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QMoA-023 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3.6 |
| QMoA-023 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         21.7 |
| QMoA-023 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.4 |
| QMoA-023 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.8 |
| QMoA-026 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.3 |
| QMoA-026 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          3   |
| QMoA-026 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         19.9 |
| QMoA-026 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.4 |
| QMoA-026 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          9.5 |
| QMoA-029 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QMoA-029 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.9 |
| QMoA-029 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.9 |
| QMoA-029 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QMoA-029 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.5 |
| QMoA-032 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.5 |
| QMoA-032 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.7 |
| QMoA-032 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         21.7 |
| QMoA-032 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          5.4 |
| QMoA-032 | qwen3.6-27b             |      0.4908 |        3 |          3 |           3 |     0.018 |         18.2 |
| QMoA-035 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.2 |
| QMoA-035 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.3 |
| QMoA-035 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         24.9 |
| QMoA-035 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QMoA-035 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.8 |
| QMoA-038 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QMoA-038 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          1.8 |
| QMoA-038 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         20.8 |
| QMoA-038 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         18.3 |
| QMoA-038 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.7 |
| QMoA-043 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.6 |
| QMoA-043 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.8 |
| QMoA-043 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.9 |
| QMoA-043 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QMoA-043 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |         13   |
| QMoA-046 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.8 |
| QMoA-046 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.1 |
| QMoA-046 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23   |
| QMoA-046 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.3 |
| QMoA-046 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          6.6 |
| QMoA-049 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          6.1 |
| QMoA-049 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.2 |
| QMoA-049 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         26.8 |
| QMoA-049 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         20.3 |
| QMoA-049 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          7.2 |
| QMoA-052 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          3.8 |
| QMoA-052 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.3 |
| QMoA-052 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         23.9 |
| QMoA-052 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.3 |
| QMoA-052 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          9.9 |
| QMoA-055 | llama-3.3-70b-versatile |      0.5    |        3 |          3 |           3 |     0     |          5.7 |
| QMoA-055 | llama-4-scout-17b       |      0.5    |        3 |          3 |           3 |     0     |          2.1 |
| QMoA-055 | qwen3-32b               |      0.5    |        3 |          3 |           3 |     0     |         17   |
| QMoA-055 | qwen3.6-27b             |      0.5    |        3 |          3 |           3 |     0     |         19.2 |
| QMoA-055 | mistral-small-latest    |      0.5    |        3 |          3 |           3 |     0     |          8.6 |

---

## 🔥 Heatmap: Model × Metric

![TRACE-Reason Evaluation Heatmap](/home/heril/Trace/Trace-REASON/outputs/eval_onco_v1/eval_heatmap.png)

---

## 📝 Key Findings

- **Best overall model:** groq/llama-3.3-70b-versatile (composite = 0.5000)
- **Lowest hallucination rate:** groq/llama-3.3-70b-versatile (0.000)
- **Fastest model:** groq/llama-4-scout-17b (2.7s avg)
- **Most faithful:** groq/llama-3.3-70b-versatile (3.00/5)

---

## ℹ️ Methodology

- **Backbone temperature:** 0.0 (deterministic, reproducible)
- **Judge temperature:** 0.0
- **Judge rotation:** Each model is scored by a judge from a different provider
- **Hallucination rate:** atomic claims extracted via sentence splitting; unsupported claims = those not grounded in the evidence package
- **Composite formula:** `(F + C₁ + C₂) / 3 × (1 − H)` where F=Faithfulness, C₁=Correctness, C₂=Completeness, H=Hallucination rate
