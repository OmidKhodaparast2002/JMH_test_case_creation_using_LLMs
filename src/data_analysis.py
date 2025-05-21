from typing import Dict, List
import json
import os
import statistics
import data_collection

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

def calc_stat_on_data(projects: List[Dict], number_of_runs: int, output_path: str):
    analysed_projects = []
    
    for project in projects:
        project_dict = {}
        project_dict["name"] = project["name"]
        project_dict["total_num_of_benchmarks"] = []
        project_dict["num_of_benchmarks_compiled"] = []
        project_dict["num_of_benchmarks_executed"] = []
        project_dict["compilation_rate"] = []
        project_dict["execution_rate"] = []
        for i in range(1, number_of_runs + 1):
            compilation_rate = project[f"run_{i}"]["num_of_benchmarks_compiled"] / project[f"run_{i}"]["total_num_of_benchmarks"]
            execution_rate = project[f"run_{i}"]["num_of_benchmarks_executed"] / project[f"run_{i}"]["num_of_benchmarks_compiled"]

            project_dict["total_num_of_benchmarks"].append(project[f"run_{i}"]["total_num_of_benchmarks"])
            project_dict["num_of_benchmarks_compiled"].append(project[f"run_{i}"]["num_of_benchmarks_compiled"])
            project_dict["num_of_benchmarks_executed"].append(project[f"run_{i}"]["num_of_benchmarks_executed"])

            project_dict["compilation_rate"].append(round(compilation_rate, 2))
            project_dict["execution_rate"].append(round(execution_rate, 2))

        analysed_projects.append(project_dict)
    
    # Calculate mean and standard deviation for each project
    for project in analysed_projects:
        project["total_num_of_benchmarks_mean"] = statistics.mean(project["total_num_of_benchmarks"])
        project["total_num_of_benchmarks_std"] = statistics.stdev(project["total_num_of_benchmarks"])
        project["num_of_benchmarks_compiled_mean"] = statistics.mean(project["num_of_benchmarks_compiled"])
        project["num_of_benchmarks_compiled_std"] = statistics.stdev(project["num_of_benchmarks_compiled"])
        project["num_of_benchmarks_executed_mean"] = statistics.mean(project["num_of_benchmarks_executed"])
        project["num_of_benchmarks_executed_std"] = statistics.stdev(project["num_of_benchmarks_executed"])
        project["compilation_rate_mean"] = statistics.mean(project["compilation_rate"])
        project["compilation_rate_std"] = statistics.stdev(project["compilation_rate"])
        project["execution_rate_mean"] = statistics.mean(project["execution_rate"])
        project["execution_rate_std"] = statistics.stdev(project["execution_rate"])

    try:
        data_collection.write_collected_data_in_json(analysed_projects, output_path)
    except Exception as e:
        print(f"Failed to write to {output_path}: {e}")

    return analysed_projects
    