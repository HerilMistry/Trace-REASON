import pandas as pd
from eval.question_templates import generate_extended_bank

def main():
    print("Generating TRACE-Onco-19 questions...")
    questions = generate_extended_bank(suite="TRACE-Onco-19")
    
    data = []
    for q in questions:
        # q.question_id, q.enzyme, q.text
        data.append({
            "Question ID": q.question_id,
            "Enzyme Target": q.enzyme,
            "Question Type": q.question_id.split("-")[0], # QAS, QMoA, QDA
            "Question Text": q.text
        })
        
    df = pd.DataFrame(data)
    
    output_excel = "outputs/eval_onco_v1/TRACE_Onco_19_Questions.xlsx"
    output_csv = "outputs/eval_onco_v1/TRACE_Onco_19_Questions.csv"
    
    df.to_excel(output_excel, index=False)
    df.to_csv(output_csv, index=False)
    
    print(f"Saved {len(questions)} questions to {output_excel}")
    print(f"Saved {len(questions)} questions to {output_csv}")

if __name__ == "__main__":
    main()
