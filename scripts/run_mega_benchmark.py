"""
run_mega_benchmark.py
=====================
Cumulative benchmark across ALL question sources:
  1. Fixed bank  (Q1–Q8)   — LRRK2, GSK3B, BACE1, MAO-B (core)
  2. Mutation bank (Q9–Q23) — 10 cancer/neuro/rare targets from UniProt
  3. CSV-derived questions  — templated from enzyme_backbone_full.csv
     • enzymes with approved drugs + pathogenic variants  → mutation Q
     • enzymes with approved drugs only                   → druggability Q
     • enzymes with reaction + disease                    → mechanism Q

Runs 4 models (no Gemini):
  groq/llama-3.3-70b-versatile
  groq/llama-4-scout-17b
  qwen/qwen3-32b
  mistral/mistral-small-latest

Output:
  outputs/mega_benchmark_results.xlsx   ← rich multi-sheet Excel
  outputs/mega_benchmark.log            ← full run log for manual verification

Usage:
  python3 scripts/run_mega_benchmark.py
  python3 scripts/run_mega_benchmark.py --max-csv 100   # limit CSV questions
"""

from __future__ import annotations

import sys, os, time, logging, argparse, textwrap
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dotenv import load_dotenv
load_dotenv()

# ── Logging: both file and console ──────────────────────────────────────────
LOG_PATH = os.path.join(_ROOT, "outputs", "mega_benchmark.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

from eval.questions import get_questions, EvalQuestion
from eval.model_registry import chat

# ── Models ───────────────────────────────────────────────────────────────────
MODELS = [
    "groq/gpt-oss-20b",  # OpenAI OSS 20B via Groq
]
MODEL_LABELS = {
    "groq/llama-3.3-70b-versatile":          "LLaMA-3.3-70B",
    "groq/llama-4-scout-17b":                "LLaMA-4-Scout-17B",
    "groq/llama-3.1-8b-instant":             "LLaMA-3.1-8B",
    "groq/gemma2-9b-it":                     "Gemma2-9B",
    "groq/deepseek-r1-distill-llama-70b":    "DeepSeek-R1-70B",
    "groq/gpt-oss-20b":                       "GPT-OSS-20B",
    "qwen/qwen3-32b":                        "Qwen3-32B",
    "mistral/mistral-small-latest":          "Mistral-Small",
}

SYSTEM_PROMPT = (
    "You are an expert molecular biologist, enzymologist, and pharmacologist. "
    "Answer rigorously using the evidence provided. Focus on mechanism, "
    "clinical relevance, mutation effects, and drug interactions. Be thorough but concise."
)


# ── Simple evidence stub for CSV-derived questions ───────────────────────────
class SimpleEvidence:
    """Lightweight stand-in for EvidencePackage used by CSV-sourced questions."""
    def __init__(self, row):
        self.gene_symbol = str(row.get("gene_symbol", ""))
        self.disease_indication = str(row.get("all_diseases", ""))[:200]
        self.variants = str(row.get("key_pathogenic_variants", ""))[:300]
        self.drugs = str(row.get("all_drugs", ""))[:300]
        self.reaction = str(row.get("enzymatic_reaction", ""))[:300]
        self.active_site = str(row.get("active_site_residues", ""))[:200]
        self.druggability = str(row.get("druggability_assessment", ""))[:200]
        self.uniprot = str(row.get("uniprot_url", ""))

    def summary(self) -> str:
        lines = [
            f"Gene: {self.gene_symbol}",
            f"Disease associations: {self.disease_indication}",
        ]
        if self.variants and self.variants not in ("nan", ""):
            lines.append(f"Pathogenic variants: {self.variants}")
        if self.drugs and self.drugs not in ("nan", ""):
            lines.append(f"Known drugs: {self.drugs}")
        if self.reaction and self.reaction not in ("nan", ""):
            lines.append(f"Reaction: {self.reaction}")
        if self.active_site and self.active_site not in ("nan", ""):
            lines.append(f"Active site: {self.active_site}")
        if self.druggability and self.druggability not in ("nan", ""):
            lines.append(f"Druggability: {self.druggability}")
        lines.append(f"UniProt: {self.uniprot}")
        return "\n".join(lines)


class CSVQuestion:
    """Mimics EvalQuestion interface for CSV-sourced questions."""
    def __init__(self, qid, text, gene, mutation, qtype, evidence: SimpleEvidence, disease):
        self.question_id = qid
        self.text = text
        self.enzyme = gene
        self.mutation = mutation
        self.qtype = qtype
        self.evidence = evidence
        self.disease = disease

    def evidence_summary(self) -> str:
        return self.evidence.summary()

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "text": self.text,
            "enzyme": self.enzyme,
            "mutation": self.mutation,
        }


# ── CSV question generator ────────────────────────────────────────────────────
def generate_csv_questions(max_total: int = 200) -> list[CSVQuestion]:
    csv_path = os.path.join(_ROOT, "data", "enzyme_backbone_full.csv")
    df = pd.read_csv(csv_path, low_memory=False)
    log.info("Loaded CSV: %d enzymes", len(df))

    questions = []
    idx = 1
    per_type = max_total // 3

    # Helper flags
    def has_val(s):
        return pd.notna(s) and str(s).strip() not in ("", "nan", "NaN")

    # ── TYPE 1: Mutation questions (has drug + pathogenic variant) ────────────
    mut_df = df[
        df["all_drugs"].apply(has_val) &
        df["key_pathogenic_variants"].apply(has_val) &
        ~df["key_pathogenic_variants"].astype(str).str.startswith("No ") &
        ~df["key_pathogenic_variants"].astype(str).str.startswith("gnomAD")
    ].head(per_type)

    for _, row in mut_df.iterrows():
        ev = SimpleEvidence(row)
        gene = str(row["gene_symbol"])
        enzyme_name = str(row["enzyme_name"]).split("(")[0].strip()[:60]
        variants = str(row["key_pathogenic_variants"])[:120]
        drugs = str(row["all_drugs"]).split(";")[0].strip()
        disease = str(row["all_diseases"]).split(";")[0].strip()[:80]

        text = (
            f"Using the supplied evidence, explain the pathogenic mechanism of the "
            f"variant(s) {variants[:80]} in {enzyme_name} ({gene}). "
            f"How do these mutations alter enzymatic function, and what is the "
            f"rationale for targeting this enzyme with drugs such as {drugs} "
            f"in the context of {disease}?"
        )
        questions.append(CSVQuestion(
            f"CSV-MUT-{idx:04d}", text, gene, variants[:60],
            "Mutation", ev, disease
        ))
        idx += 1

    log.info("Generated %d CSV mutation questions", len(questions))

    # ── TYPE 2: Druggability questions (has approved/clinical drug, no variant) ─
    drug_df = df[
        df["all_drugs"].apply(has_val) &
        df["druggability_tier"].isin(["Approved target", "Clinical trial target"]) &
        df["enzymatic_reaction"].apply(has_val)
    ].head(per_type)

    t2_start = len(questions)
    for _, row in drug_df.iterrows():
        ev = SimpleEvidence(row)
        gene = str(row["gene_symbol"])
        enzyme_name = str(row["enzyme_name"]).split("(")[0].strip()[:60]
        drugs = str(row["all_drugs"])[:200]
        tier = str(row["druggability_tier"])
        disease = str(row["all_diseases"]).split(";")[0].strip()[:80]
        reaction = str(row["enzymatic_reaction"])[:150]

        text = (
            f"Assess the druggability of {enzyme_name} ({gene}) as a therapeutic "
            f"target (druggability tier: {tier}). "
            f"Its catalytic reaction is: {reaction}. "
            f"Using the supplied evidence, evaluate: "
            f"(1) what active-site features make it druggable; "
            f"(2) the mechanism of action of known drugs ({drugs[:100]}); "
            f"(3) the therapeutic rationale in {disease}."
        )
        questions.append(CSVQuestion(
            f"CSV-DRUG-{idx:04d}", text, gene, None,
            "Druggability", ev, disease
        ))
        idx += 1

    log.info("Generated %d CSV druggability questions", len(questions) - t2_start)

    # ── TYPE 3: Mechanism questions (has reaction + disease, any tier) ────────
    mech_df = df[
        df["enzymatic_reaction"].apply(has_val) &
        df["all_diseases"].apply(has_val) &
        df["active_site_residues"].apply(has_val) &
        ~df["enzyme_id"].isin(mut_df["enzyme_id"]) &
        ~df["enzyme_id"].isin(drug_df["enzyme_id"])
    ].head(per_type)

    t3_start = len(questions)
    for _, row in mech_df.iterrows():
        ev = SimpleEvidence(row)
        gene = str(row["gene_symbol"])
        enzyme_name = str(row["enzyme_name"]).split("(")[0].strip()[:60]
        reaction = str(row["enzymatic_reaction"])[:200]
        active_site = str(row["active_site_residues"])[:150]
        disease = str(row["all_diseases"]).split(";")[0].strip()[:80]
        ec = str(row["ec_number"])

        text = (
            f"Describe the catalytic mechanism of {enzyme_name} ({gene}, EC {ec}). "
            f"Reaction: {reaction}. "
            f"Key active-site residues: {active_site}. "
            f"Explain how the active-site architecture enables substrate processing "
            f"and discuss its relevance as a drug target in {disease}, "
            f"referencing the supplied evidence."
        )
        questions.append(CSVQuestion(
            f"CSV-MECH-{idx:04d}", text, gene, None,
            "Mechanism", ev, disease
        ))
        idx += 1

    log.info("Generated %d CSV mechanism questions", len(questions) - t3_start)
    log.info("Total CSV questions: %d", len(questions))
    return questions


# ── Prompt builder ────────────────────────────────────────────────────────────
def build_messages(q) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"EVIDENCE PACKAGE:\n{q.evidence_summary()}\n\n"
            f"QUESTION [{q.question_id}]:\n{q.text}"
        )},
    ]


# ── Simple keyword scorer ─────────────────────────────────────────────────────
FIXED_KEYWORDS = {
    "Q1":  ["G2019S","kinase","gain-of-function","phosphorylation"],
    "Q2":  ["Km","kcat","Tideglusib","tau"],
    "Q3":  ["L776V","A673T","BACE1","amyloid"],
    "Q4":  ["Rab8A","Rab10","lysosomal","alpha-synuclein"],
    "Q5":  ["Ser396","Thr231","neurofibrillary","kcat/Km"],
    "Q6":  ["Asp93","Asp289","Verubecestat","clinical"],
    "Q7":  ["FAD","irreversible","covalent","700"],
    "Q8":  ["LRRK2","BACE1","MAO-B","IC50"],
    "Q9":  ["L858R","T790M","resistance","gefitinib"],
    "Q10": ["C797S","osimertinib","covalent"],
    "Q11": ["T315I","imatinib","ponatinib","BCR-ABL"],
    "Q12": ["V600E","constitutive","vemurafenib","MEK"],
    "Q13": ["R132H","2-hydroxyglutarate","neomorphic","IDH1"],
    "Q14": ["R140Q","R172K","enasidenib","IDH2"],
    "Q15": ["H1047R","E545K","PI3K","alpelisib"],
    "Q16": ["D835Y","ITD","midostaurin","FLT3"],
    "Q17": ["G309D","mitophagy","PINK1","Parkin"],
    "Q18": ["Q456X","truncation","PINK1","kinase stability"],
    "Q19": ["E280A","gamma-secretase","amyloid","Abeta"],
    "Q20": ["M146L","PSEN1","familial","APP"],
    "Q21": ["N370S","L444P","glucocerebrosidase","Gaucher"],
    "Q22": ["N370S","Parkinson","lysosomal","GBA1"],
    "Q23": ["enzyme replacement","imiglucerase","substrate reduction"],
}

def score_response(qid: str, gene: str, mutation: str | None, response: str) -> tuple[int, int]:
    """Returns (hits, max_possible)."""
    text = response.lower()
    if qid in FIXED_KEYWORDS:
        kws = FIXED_KEYWORDS[qid]
        return sum(1 for k in kws if k.lower() in text), len(kws)
    # CSV questions: score by gene mention + mutation mention (if applicable)
    score, max_s = 0, 2
    if gene.lower() in text:
        score += 1
    if mutation and any(part.lower() in text for part in mutation.split("/")):
        score += 1
    elif not mutation:
        max_s = 1
        score = 1 if gene.lower() in text else 0
    return score, max_s


# ── Excel writer ──────────────────────────────────────────────────────────────
def write_excel(rows: list[dict], all_questions: list, output_path: str):
    df = pd.DataFrame(rows)

    # ── Questions reference sheet ─────────────────────────────────────────────
    q_rows = []
    for q in all_questions:
        source = "Fixed" if not q.question_id.startswith("CSV") else q.question_id.split("-")[1]
        qtype = getattr(q, "qtype", ("Mutation" if (not q.question_id.startswith("CSV") and q.mutation) else "Core"))
        disease = getattr(q, "disease", getattr(getattr(q, "evidence", None), "disease", None))
        if hasattr(disease, "indication"):
            disease_str = disease.indication
        else:
            disease_str = str(disease) if disease else ""
        q_rows.append({
            "Question ID": q.question_id,
            "Source": source,
            "Type": qtype,
            "Enzyme/Gene": q.enzyme,
            "Mutation": q.mutation or "N/A",
            "Disease": disease_str[:100],
            "Question Text": q.text,
        })
    df_questions = pd.DataFrame(q_rows)

    # ── Summary by model × source ─────────────────────────────────────────────
    summary_rows = []
    for model in df["Model"].unique():
        mdf = df[df["Model"] == model]
        for src in ["Fixed", "MUT", "DRUG", "MECH", "All"]:
            if src == "All":
                sub = mdf
            elif src == "Fixed":
                sub = mdf[~mdf["Question ID"].str.startswith("CSV")]
            else:
                sub = mdf[mdf["Question ID"].str.startswith(f"CSV-{src}")]
            if len(sub) == 0:
                continue
            kw_hits = sub["Keyword Hits"].sum()
            kw_max  = sub["Keyword Max"].sum()
            summary_rows.append({
                "Model":           model,
                "Question Source": src,
                "Questions":       len(sub),
                "Successful Calls":sub["Success"].sum(),
                "Failed Calls":    (~sub["Success"]).sum(),
                "Keyword Hits":    int(kw_hits),
                "Keyword Max":     int(kw_max),
                "Keyword Score %": round(100 * kw_hits / kw_max, 1) if kw_max else 0,
                "Avg Latency (s)": round(sub["Latency (s)"].mean(), 2),
                "Avg Tokens":      round(sub["Tokens"].mean(), 0),
                "Total Tokens":    int(sub["Tokens"].sum()),
            })
    df_summary = pd.DataFrame(summary_rows)

    # ── Model leaderboard (overall) ───────────────────────────────────────────
    leader_rows = []
    for model in df["Model"].unique():
        mdf = df[df["Model"] == model]
        kw_hits = mdf["Keyword Hits"].sum()
        kw_max  = mdf["Keyword Max"].sum()
        leader_rows.append({
            "Rank":            0,
            "Model":           model,
            "Total Questions": len(mdf),
            "Successful":      int(mdf["Success"].sum()),
            "Keyword Score %": round(100 * kw_hits / kw_max, 1) if kw_max else 0,
            "Avg Latency (s)": round(mdf["Latency (s)"].mean(), 2),
            "Avg Tokens":      round(mdf["Tokens"].mean(), 0),
        })
    df_leader = pd.DataFrame(leader_rows).sort_values("Keyword Score %", ascending=False)
    df_leader["Rank"] = range(1, len(df_leader) + 1)

    # ── Per-type performance pivot ────────────────────────────────────────────
    df["Q_Type"] = df.apply(
        lambda r: ("Mutation" if r["Mutation"] != "N/A" else "Core/Mechanism"),
        axis=1
    )
    pivot = df.pivot_table(
        index=["Question ID", "Enzyme", "Mutation", "Q_Type"],
        columns="Model", values="Keyword Score %", aggfunc="first"
    ).reset_index()

    # ── Write Excel ───────────────────────────────────────────────────────────
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_leader.to_excel(writer, sheet_name="🏆 Leaderboard", index=False)
        df_summary.to_excel(writer, sheet_name="📊 Summary by Source", index=False)
        df_questions.to_excel(writer, sheet_name="📋 All Questions", index=False)
        pivot.to_excel(writer, sheet_name="🔢 Score Pivot", index=False)
        df.to_excel(writer, sheet_name="📝 Raw Results", index=False)

        # Per-model sheets with full responses
        for model in df["Model"].unique():
            safe = model[:28]
            cols = ["Question ID","Q_Type","Enzyme","Mutation","Disease",
                    "Success","Latency (s)","Tokens","Keyword Hits","Keyword Max",
                    "Keyword Score %","Response"]
            df[df["Model"] == model][cols].to_excel(writer, sheet_name=safe, index=False)

        # Apply column widths
        for sheet_name, sheet in writer.sheets.items():
            for col in sheet.columns:
                max_len = max((len(str(cell.value or "")) for cell in col), default=10)
                sheet.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

    log.info("Excel saved → %s", output_path)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-csv", type=int, default=37,
                        help="Max CSV-derived questions (split ~3 ways; default 37 → 60 total)")
    args = parser.parse_args()

    log.info("=" * 70)
    log.info("TRACE-Reason Mega Benchmark")
    log.info("=" * 70)

    # ── Collect all questions ─────────────────────────────────────────────────
    fixed_qs = get_questions()
    log.info("Fixed questions loaded: %d", len(fixed_qs))

    csv_qs = generate_csv_questions(max_total=args.max_csv)
    log.info("CSV questions generated: %d", len(csv_qs))

    all_questions = fixed_qs + csv_qs
    log.info("TOTAL questions: %d", len(all_questions))
    log.info("Models to run: %s", [MODEL_LABELS[m] for m in MODELS])
    log.info("Total API calls: %d", len(all_questions) * len(MODELS))
    log.info("Estimated time: ~%.0f min", len(all_questions) * len(MODELS) * 3 / 60)

    rows = []
    total_calls = len(MODELS) * len(all_questions)
    done = 0

    for model_key in MODELS:
        label = MODEL_LABELS[model_key]
        log.info("─" * 60)
        log.info("MODEL: %s", label)
        log.info("─" * 60)

        for q in all_questions:
            done += 1
            log.info("[%d/%d] %s → %s (%s)", done, total_calls, label, q.question_id, q.enzyme)

            messages = build_messages(q)
            t0 = time.perf_counter()
            try:
                resp = chat(model_key, messages, temperature=0.0, max_tokens=1024)
                # If daily token limit hit, skip this model
                if not resp.success and resp.error and "tokens per day" in str(resp.error).lower():
                    log.warning("  TPD limit hit for %s — skipping remaining questions for this model", label)
                    rows.append({
                        "Model": label, "Question ID": q.question_id,
                        "Q_Type": getattr(q, "qtype", "Core"),
                        "Source": "Fixed" if not q.question_id.startswith("CSV") else q.question_id.split("-")[1],
                        "Enzyme": q.enzyme, "Mutation": q.mutation or "N/A",
                        "Disease": str(getattr(q, "disease", ""))[:100],
                        "Question Text": q.text, "Success": False,
                        "Latency (s)": 0, "Tokens": 0,
                        "Keyword Hits": 0, "Keyword Max": score_response(q.question_id, q.enzyme, q.mutation, "")[1],
                        "Keyword Score %": 0.0,
                        "Response": f"[SKIPPED] TPD limit: {resp.error}",
                    })
                    # fill remaining questions for this model as skipped
                    remaining_idx = all_questions.index(q)
                    for rq in all_questions[remaining_idx + 1:]:
                        done += 1
                        _, rmax = score_response(rq.question_id, rq.enzyme, rq.mutation, "")
                        rdisease = str(getattr(rq, "disease", ""))[:100]
                        rows.append({
                            "Model": label, "Question ID": rq.question_id,
                            "Q_Type": getattr(rq, "qtype", "Core"),
                            "Source": "Fixed" if not rq.question_id.startswith("CSV") else rq.question_id.split("-")[1],
                            "Enzyme": rq.enzyme, "Mutation": rq.mutation or "N/A",
                            "Disease": rdisease, "Question Text": rq.text,
                            "Success": False, "Latency (s)": 0, "Tokens": 0,
                            "Keyword Hits": 0, "Keyword Max": rmax,
                            "Keyword Score %": 0.0,
                            "Response": "[SKIPPED] TPD limit reached",
                        })
                    log.warning("  Skipped %d questions for %s", len(all_questions) - remaining_idx - 1, label)
                    break  # move to next model
            except Exception as e:
                log.error("  EXCEPTION: %s", e)
                resp = type("R", (), {
                    "success": False, "content": "", "error": str(e),
                    "latency_seconds": time.perf_counter() - t0, "token_count": 0
                })()
            latency = time.perf_counter() - t0

            kw_hits, kw_max = score_response(
                q.question_id, q.enzyme, q.mutation, resp.content if resp.success else ""
            )
            kw_pct = round(100 * kw_hits / kw_max, 1) if kw_max else 0.0

            # Disease string
            ev = getattr(q, "evidence", None)
            if ev and hasattr(ev, "disease") and hasattr(ev.disease, "indication"):
                disease_str = ev.disease.indication
            else:
                disease_str = getattr(q, "disease", "")

            rows.append({
                "Model":           label,
                "Question ID":     q.question_id,
                "Q_Type":          getattr(q, "qtype", "Core"),
                "Source":          "Fixed" if not q.question_id.startswith("CSV") else q.question_id.split("-")[1],
                "Enzyme":          q.enzyme,
                "Mutation":        q.mutation or "N/A",
                "Disease":         str(disease_str)[:100],
                "Question Text":   q.text,
                "Success":         resp.success,
                "Latency (s)":     round(latency, 2),
                "Tokens":          resp.token_count,
                "Keyword Hits":    kw_hits,
                "Keyword Max":     kw_max,
                "Keyword Score %": kw_pct,
                "Response":        resp.content if resp.success else f"[ERROR] {getattr(resp, 'error', 'unknown')}",
            })

            log.info("  ✓ Success=%s  Latency=%.2fs  Tokens=%d  Keywords=%d/%d (%.0f%%)",
                     resp.success, latency, resp.token_count, kw_hits, kw_max, kw_pct)

            time.sleep(2.5)  # extra breathing room for Qwen rate limits

    # ── Save results ──────────────────────────────────────────────────────────
    output_path = os.path.join(_ROOT, "outputs", "mega_benchmark_results.xlsx")
    write_excel(rows, all_questions, output_path)

    log.info("=" * 70)
    log.info("DONE — %d rows saved to %s", len(rows), output_path)
    log.info("Log file: %s", LOG_PATH)
    log.info("=" * 70)

    # Print quick leaderboard to stdout
    df = pd.DataFrame(rows)
    print("\n" + "=" * 60)
    print("LEADERBOARD (Overall Keyword Score)")
    print("=" * 60)
    for model in df["Model"].unique():
        mdf = df[df["Model"] == model]
        hits = mdf["Keyword Hits"].sum()
        mx   = mdf["Keyword Max"].sum()
        pct  = round(100 * hits / mx, 1) if mx else 0
        lat  = round(mdf["Latency (s)"].mean(), 2)
        print(f"  {model:22s}  {pct:5.1f}%   avg_latency={lat}s   n={len(mdf)}")
    print(f"\n📊 Excel  → {output_path}")
    print(f"📋 Log    → {LOG_PATH}\n")


if __name__ == "__main__":
    main()
