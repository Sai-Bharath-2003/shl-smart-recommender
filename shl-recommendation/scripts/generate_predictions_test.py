import pandas as pd
import requests
import os

# 1. Setup absolute paths to avoid confusion
current_dir = os.path.dirname(os.path.abspath(__file__))
# Based on your tree: shl-recommendation/scripts/data
data_dir = os.path.join(current_dir, 'data') 

test_input = os.path.join(data_dir, 'Test-Set.csv')
final_output = os.path.join(data_dir, 'Final_Submission_Predictions.csv')

print(f"--- SCRIPT STARTED ---")
print(f"Checking for input file at: {test_input}")

if not os.path.exists(test_input):
    print(f"ERROR: Cannot find 'Test-Set.csv' in {data_dir}")
    print("Check if the file is named exactly 'Test-Set.csv' (case sensitive).")
else:
    print(f"SUCCESS: Found input file. Loading data...")
    df_test = pd.read_csv(test_input)
    test_queries = df_test['Query'].unique()
    rows = []

    print(f"Processing {len(test_queries)} unique queries...")

    for i, query in enumerate(test_queries):
        try:
            # Hit your LIVE Uvicorn server
            response = requests.post(
                "http://localhost:8000/recommend", 
                json={"query": query},
                timeout=30
            )
            recommendations = response.json().get('recommended_assessments', [])
            
            for rec in recommendations[:10]:
                rows.append({
                    'Query': query, 
                    'Assessment_Name': rec['name'],
                    'Assessment_url': rec['url']
                })
            print(f"[{i+1}/9] Processed: {query[:30]}...")
            
        except Exception as e:
            print(f"FAILED query {i+1}: {e}")

    # 2. Save the file and FORCE a confirmation message
    if rows:
        df_out = pd.DataFrame(rows)
        df_out.to_csv(final_output, index=False)
        print(f"\n--- FILE CREATED SUCCESSFULLY ---")
        print(f"Location: {final_output}")
        print(f"Total rows saved: {len(df_out)}")
    else:
        print("\n--- ERROR: No recommendations were gathered. Is your backend server running? ---")