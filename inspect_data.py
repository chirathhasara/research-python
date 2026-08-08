import pandas as pd

df = pd.read_csv(r"e:\Research\Coding\python\form_B_phase_2\formula_b_phase2_results.csv")
print("Workloads:", df['Workload'].unique())
print("Patterns:", df['Pattern'].unique())
print("Strategies (sample):", df['Strategy'].unique()[:10])

# Check rows for N=10000000
df_10m = df[df['Workload'] == 10000000]
print("N=10M patterns:", df_10m['Pattern'].unique())
