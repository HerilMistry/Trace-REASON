"""
run_mutation_benchmark.py
=========================
Runs all 23 eval questions (Q1-Q23, including the new mutation bank Q9-Q23)
against 4 models (LLaMA-3.3-70B, LLaMA-4-Scout, Qwen3-32B, Mistral-Small),
saves raw results + summary to outputs/mutation_benchmark_results.xlsx
"""

from __future__ import annotations

import sys, os, time, logging

# ── path setup ──────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from eval.questions import get_questions
from eval.model_registry import chat, MODELS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
MODELS_TO_RUN = [
    "groq/llama-3.3-70b-versatile",
    "groq/llama-4-scout-17b",
    "qwen/qwen3-32b",
    "mistral/mistral-small-latest",
]
MODEL_LABELS = {
    "groq/llama-3.3-70b-versatile": "LLaMA-3.3-70B",
    "groq/llama-4-scout-17b":       "LLaMA-4-Scout-17B",
    "qwen/qwen3-32b":               "Qwen3-32B",
    "mistral/mistral-small-latest": "Mistral-Small",
}
OUTPUT_PATH = os.path.join(_ROOT, "outputs", "mutation_benchmark_results.xlsx")

SYSTEM_PROMPT = (
    "You are an expert molecular biologist and pharmacologist. "
    "Answer the question rigorously using the evidence package provided. "
    "Be concise but thorough — focus on mechanism, clinical relevance, and drug interactions."
)

# ── Build prompt for a question ──────────────────────────────────────────────
def build_prompt(q) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": (
            f"EVIDENCE PACKAGE:\n{q.evidence_summary()}\n\n"
            f"QUESTION [{q.question_id}]:\n{q.text}"
        )},
    ]

# ── Scoring heuristic (keyword-based proxy) ──────────────────────────────────
MUTATION_KEYWORDS = {
    "Q1":  ["G2019S", "kinase", "gain-of-function", "phosphorylation"],
    "Q2":  ["Km", "kcat", "Tideglusib", "tau"],
    "Q3":  ["L776V", "A673T", "BACE1", "amyloid"],
    "Q4":  ["Rab8A", "Rab10", "lysosomal", "alpha-synuclein"],
    "Q5":  ["Ser396", "Thr231", "neurofibrillary", "kcat/Km"],
    "Q6":  ["Asp93", "Asp289", "Verubecestat", "clinical"],
    "Q7":  ["FAD", "irreversible", "covalent", "700"],
    "Q8":  ["LRRK2", "BACE1", "MAO-B", "IC50"],
    "Q9":  ["L858R", "T790M", "resistance", "gefitinib"],
    "Q10": ["C797S", "osimertinib", "covalent"],
    "Q11": ["T315I", "imatinib", "ponatinib", "BCR-ABL"],
    "Q12": ["V600E", "constitutive", "vemurafenib", "MEK"],
    "Q13": ["R132H", "2-hydroxyglutarate", "neomorphic", "IDH1"],
    "Q14": ["R140Q", "R172K", "enasidenib", "IDH2"],
    "Q15": ["H1047R", "E545K", "PI3K", "alpelisib"],
    "Q16": ["D835Y", "ITD", "midostaurin", "FLT3"],
    "Q17": ["G309D", "mitophagy", "PINK1", "Parkin"],
    "Q18": ["Q456X", "truncation", "PINK1", "kinase stability"],
    "Q19": ["E280A", "gamma-secretase", "amyloid", "Abeta"],
    "Q20": ["M146L", "PSEN1", "familial", "APP"],
    "Q21": ["N370S", "L444P", "glucocerebrosidase", "Gaucher"],
    "Q22": ["N370S", "Parkinson", "lysosomal", "GBA1"],
    "Q23": ["enzyme replacement", "imiglucerase", "substrate reduction"],
}

def score_response(qid: str, response: str) -> int:
    """Simple keyword-hit score 0-4 as a fast proxy for correctness."""
    keywords = MUTATION_KEYWORDS.get(qid, [])
    if not keywords:
        return 0
    text_lower = response.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    questions = get_questions()
    log.info("Loaded %d questions", len(questions))

    rows = []
    total = len(MODELS_TO_RUN) * len(questions)
    done = 0

    for model_key in MODELS_TO_RUN:
        label = MODEL_LABELS[model_key]
        log.info("=== Model: %s ===", label)

        for q in questions:
            done += 1
            log.info("[%d/%d] %s → %s", done, total, label, q.question_id)

            messages = build_prompt(q)
            t0 = time.perf_counter()
            resp = chat(model_key, messages, temperature=0.0, max_tokens=1024)
            latency = time.perf_counter() - t0

            keyword_score = score_response(q.question_id, resp.content)
            category = "Mutation" if q.question_id.startswith("Q") and int(q.question_id[1:]) >= 9 else "Core"

            rows.append({
                "Model":          label,
                "Question ID":    q.question_id,
                "Category":       category,
                "Enzyme":         q.enzyme,
                "Mutation":       q.mutation or "N/A",
                "Disease":        q.evidence.disease.indication,
                "Question Text":  q.text,
                "Response":       resp.content if resp.success else f"[ERROR] {resp.error}",
                "Success":        resp.success,
                "Latency (s)":    round(latency, 2),
                "Tokens":         resp.token_count,
                "Keyword Score":  keyword_score,
                "Max Score":      len(MUTATION_KEYWORDS.get(q.question_id, [])),
            })

            # Brief pause to respect rate limits
            time.sleep(1.2)

    df = pd.DataFrame(rows)

    # ── Summary sheet ─────────────────────────────────────────────────────────
    summary_rows = []
    for model in df["Model"].unique():
        mdf = df[df["Model"] == model]
        for cat in ["Core", "Mutation", "All"]:
            if cat == "All":
                sub = mdf
            else:
                sub = mdf[mdf["Category"] == cat]
            total_qs   = len(sub)
            success_n  = sub["Success"].sum()
            kw_score   = sub["Keyword Score"].sum()
            kw_max     = sub["Max Score"].sum()
            avg_lat    = sub["Latency (s)"].mean()
            avg_toks   = sub["Tokens"].mean()
            summary_rows.append({
                "Model":           model,
                "Subset":          cat,
                "Questions":       total_qs,
                "Successful":      success_n,
                "Failed":          total_qs - success_n,
                "Keyword Hits":    kw_score,
                "Keyword Max":     kw_max,
                "Keyword %":       round(100 * kw_score / kw_max, 1) if kw_max else 0,
                "Avg Latency (s)": round(avg_lat, 2),
                "Avg Tokens":      round(avg_toks, 0),
            })

    df_summary = pd.DataFrame(summary_rows)

    # ── Pivot: keyword score per model × question ─────────────────────────────
    df_pivot = df.pivot_table(
        index="Question ID", columns="Model", values="Keyword Score", aggfunc="first"
    ).reset_index()
    df_pivot["Enzyme"] = df_pivot["Question ID"].map(
        {q.question_id: q.enzyme for q in questions}
    )
    df_pivot["Mutation"] = df_pivot["Question ID"].map(
        {q.question_id: (q.mutation or "N/A") for q in questions}
    )
    df_pivot["Category"] = df_pivot["Question ID"].apply(
        lambda qid: "Mutation" if int(qid[1:]) >= 9 else "Core"
    )
    cols = ["Question ID", "Category", "Enzyme", "Mutation"] + sorted(MODEL_LABELS.values())
    df_pivot = df_pivot[[c for c in cols if c in df_pivot.columns]]

    # ── Write Excel ───────────────────────────────────────────────────────────
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        df_pivot.to_excel(writer, sheet_name="Scores_Pivot", index=False)
        df.to_excel(writer, sheet_name="Raw_Results", index=False)

        # Per-model sheets
        for model in df["Model"].unique():
            safe_name = model.replace("/", "_").replace(" ", "_")[:31]
            df[df["Model"] == model].to_excel(
                writer, sheet_name=safe_name, index=False
            )

    log.info("✅  Saved %d rows → %s", len(df), OUTPUT_PATH)
    print(f"\n📊 Report saved to: {OUTPUT_PATH}")
    print(df_summary.to_string(index=False))


if __name__ == "__main__":
    main()
