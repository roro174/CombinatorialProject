
import os
import time
import pandas as pd
from isp_model import ISPModel
from handle_json import HandleJson

def run_instances(directory="/mnt/data"):
    instance_files = sorted([
        f for f in os.listdir(directory)
        if f.endswith(".json") and not f.startswith("example")
    ])
    results = []

    for file in instance_files:
        file_path = os.path.join(directory, file)
        print(f"Processing {file_path}...")
        data_handler = HandleJson(file_path)

        for model_type, question2, bridge in [
            ("Base", False, False),
            ("Q2", True, False),
            ("Bridge", False, True),
            ("Q2+Bridge", True, True)
        ]:
            for obj_func in ["OF1", "OF2"]:
                try:
                    model = ISPModel(data_handler, question2=question2, bridge=bridge)
                    start = time.time()
                    model.solve_of(verbose=False, of1=(obj_func == "OF1"))
                    end = time.time()

                    runtime = end - start
                    mip_gap = model.model.MIPGap if model.model.MIPGap is not None else float("nan")
                    obj_val = model.model.ObjVal if model.model.Status == 2 else float("nan")

                    results.append({
                        "Instance": file,
                        "Model": model_type,
                        "Objective": obj_func,
                        "Objective Value": obj_val,
                        "MIP Gap": mip_gap,
                        "Runtime (s)": runtime
                    })
                except Exception as e:
                    print(f"Error processing {file} with model {model_type} and objective {obj_func}: {e}")
                    results.append({
                        "Instance": file,
                        "Model": model_type,
                        "Objective": obj_func,
                        "Objective Value": "Error",
                        "MIP Gap": "Error",
                        "Runtime (s)": "Error"
                    })

    df = pd.DataFrame(results)
    df.to_csv("results_summary.csv", index=False)
    print("Results written to results_summary.csv")

if __name__ == "__main__":
    run_instances()
