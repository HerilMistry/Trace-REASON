import json
import pandas as pd
import os

def create_excel_report():
    input_file = "outputs/eval_drug_activesite_v2/eval_report.json"
    output_file = "outputs/eval_drug_activesite_v2/detailed_eval_report.xlsx"
    
    with open(input_file, 'r') as f:
        data = json.load(f)
        
    leaderboard = data.get('leaderboard', [])
    per_question = data.get('per_question_rows', [])
    raw_evals = data.get('raw_eval_records', [])
    
    # Extract unique questions tested
    questions_dict = {}
    for ev in raw_evals:
        q_id = ev.get('question_id')
        if q_id not in questions_dict:
            questions_dict[q_id] = {
                'Question ID': q_id,
                'Enzyme': ev.get('enzyme'),
                'Question Text': ev.get('question_text')
            }
    
    questions_df = pd.DataFrame(list(questions_dict.values()))
    
    # DataFrames
    df_leaderboard = pd.DataFrame(leaderboard)
    df_per_question = pd.DataFrame(per_question)
    
    # For raw evals, we only want useful text for details
    df_raw = pd.DataFrame([{
        'Model': ev.get('model_name'),
        'Question ID': ev.get('question_id'),
        'Success': ev.get('success'),
        'Latency (s)': ev.get('latency_seconds'),
        'Model Output (Detail)': ev.get('model_output')
    } for ev in raw_evals])
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_leaderboard.to_excel(writer, sheet_name="Leaderboard", index=False)
        df_per_question.to_excel(writer, sheet_name="Per-Question Scores", index=False)
        df_raw.to_excel(writer, sheet_name="Raw Outputs", index=False)
        questions_df.to_excel(writer, sheet_name="Questions Tested", index=False)
        
    print(f"Excel report created successfully at: {output_file}")

if __name__ == "__main__":
    create_excel_report()
