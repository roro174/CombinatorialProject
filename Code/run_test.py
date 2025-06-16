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
import sys
import time
from main import HandleJson, ISPModel

def run_test(json_file, question2, bridge):
    print(f"\n==> Testing {json_file} | Q2: {question2} | Bridge: {bridge}")
    data_handler = HandleJson(json_file)
    model = ISPModel(data_handler, question2, bridge)

    results = []
    for of2 in [False, True]:  # False = OF1, True = OF2
        objective_name = "OF2" if of2 else "OF1"
        model.model.setParam("TimeLimit", 600)  # 10 min
        start = time.time()
        model.solve_of(verbose=False, of2=of2)
        end = time.time()
        runtime = round(end - start, 2)
        mip_gap = round(model.model.MIPGap * 100, 2) if model.model.SolCount > 0 else None
        obj_val = model.model.ObjVal if model.model.SolCount > 0 else None
        results.append((objective_name, obj_val, mip_gap, runtime))

    return results

def main():
    folder = "instances"
    combinations = [
        (False, False),
        (True, False),
        (False, True),
        (True, True)
    ]

    json_files = [f for f in os.listdir(folder) if f.endswith(".json")]
    log_file = "results_summary.tsv"

    with open(log_file, "w") as log:
        log.write("Instance\tQ2\tBridge\tObjective\tObjVal\tMIPGap(%)\tRuntime(s)\n")
        for json_file in sorted(json_files):
            full_path = os.path.join(folder, json_file)
            for q2, br in combinations:
                results = run_test(full_path, q2, br)
                for objective_name, obj_val, mip_gap, runtime in results:
                    log.write(f"{json_file}\t{q2}\t{br}\t{objective_name}\t{obj_val}\t{mip_gap}\t{runtime}\n")

    print(f"\nAll tests completed. Summary saved in '{log_file}'.")

if __name__ == "__main__":
    main()
