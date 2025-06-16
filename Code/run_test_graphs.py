"""
Project of Combinatorial Optimization: ISP problem
Batch runner for testing ISP model with all configurations
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI
Datum: 16/06/2025
"""

import os
import time
from main import HandleJson, ISPModel
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def run_test(json_file, question2, bridge):
    print(f"\n==> Testing {json_file} | Q2: {question2} | Bridge: {bridge}")
    data_handler = HandleJson(json_file)
    model = ISPModel(data_handler, question2, bridge)

    results = []
    for of2 in [False, True]:  # False = OF1, True = OF2
        objective_name = "OF2" if of2 else "OF1"
        model.model.setParam("TimeLimit", 600)
        start = time.time()
        model.solve_of(verbose=False, of2=of2)
        end = time.time()

        runtime = round(end - start, 2)
        mip_gap = round(model.model.MIPGap * 100, 2) if model.model.SolCount > 0 else None
        obj_val = model.model.ObjVal if model.model.SolCount > 0 else None

        results.append({
            "Instance": os.path.basename(json_file),
            "Q2": question2,
            "Bridge": bridge,
            "Objective": objective_name,
            "ObjVal": obj_val,
            "MIPGap(%)": mip_gap,
            "Runtime(s)": runtime
        })

    return results


def generate_graphs(df):
    sns.set(style="whitegrid")
    df["Config"] = df.apply(lambda row: f"Q2={row['Q2']}|Bridge={row['Bridge']}", axis=1)

    # Runtime
    plt.figure()
    sns.barplot(data=df, x="Instance", y="Runtime(s)", hue="Config")
    plt.title("Runtime Comparison")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("runtime_comparison.png")

    # MIP Gap
    plt.figure()
    sns.barplot(data=df, x="Instance", y="MIPGap(%)", hue="Config")
    plt.title("MIP Gap Comparison")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("mipgap_comparison.png")

    # Objective values
    plt.figure()
    sns.barplot(data=df, x="Instance", y="ObjVal", hue="Objective")
    plt.title("OF1 vs OF2 Objective Values")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("objective_comparison.png")

    # Runtime for OF1 only by configuration
    df_of1 = df[df["Objective"] == "OF1"]
    plt.figure()
    sns.barplot(data=df_of1, x="Instance", y="Runtime(s)", hue="Config")
    plt.title("OF1 Runtime by Configuration")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("of1_runtime_config.png")


def main():
    folder = "instances"
    combinations = [(False, False), (True, False), (False, True), (True, True)]

    json_files = [f for f in os.listdir(folder) if f.endswith(".json")]
    all_results = []

    for json_file in sorted(json_files):
        full_path = os.path.join(folder, json_file)
        for q2, br in combinations:
            all_results.extend(run_test(full_path, q2, br))

    df = pd.DataFrame(all_results)
    df = df[df["ObjVal"].notnull()]
    generate_graphs(df)
    print("\nAll tests completed. Graphs saved as PNG.")


if __name__ == "__main__":
    main()
