from typing import Dict, List
import json
import os

def find_most_frequent_compile_errors(projects: List[Dict], list_of_compile_errors: List[str]):

    # Initialize a dictionary to store the count of each compile error
    compile_error_counts = {error: 0 for error in list_of_compile_errors}
    compile_error_counts["Other Category"] = 0

    # Count the occurrences of each compile error
    for project in projects:
        for module in project["modules"]:
            compile_erros = module.get("compile_errors", [])
            for error in compile_erros:
                if error in compile_error_counts.keys():
                    compile_error_counts[error] += 1
                else:
                    compile_error_counts["Other Category"] += 1

    # Sort the dictionary by count in descending order
    sorted_compile_errors = sorted(compile_error_counts.items(), key=lambda x: x[1], reverse=True)

    try:
        os.makedirs(os.path.join("..", "data", "analysed"), exist_ok=True)
        with open(os.path.join("..", "data", "analysed", "compile_errors.json"), "w") as f:
            json.dump(sorted_compile_errors, f, indent=4)
    except Exception as e:
        print(f"Failed to write to compile_errors.json: {e}")

    return sorted_compile_errors