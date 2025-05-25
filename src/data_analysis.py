from typing import Dict, List
import json
import os
import statistics
import data_collection
import utils
import matplotlib.pyplot as plt

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
    
def create_files_to_save_coverage_data(project_names: List[str], data_run_paths: List[str], coverage_save_path: str, llm_save_path: str, human_save_path: str):
    counter = 0
    for run_path in data_run_paths:
        counter += 1
        for project_name in project_names:
            json_format_llm = {
                "lines_missed": 0,
                "total_lines": 0
            }
            json_format_human = {
                "lines_missed": 0,
                "total_lines": 0
            }
            llm_path = os.path.join(run_path, coverage_save_path, project_name, llm_save_path)
            human_path = os.path.join(run_path, coverage_save_path, project_name, human_save_path)
            lines_missed_llm, total_lines_llm = read_coverage_values_from_user(f"data run {counter}: Enter the coverage values for {project_name} (LLM):")
            print("\n")
            lines_missed_human, total_lines_human = read_coverage_values_from_user(f"data run {counter}: Enter the coverage values for {project_name} (Human):")
            print("\n")
            json_format_llm["lines_missed"] = lines_missed_llm
            json_format_llm["total_lines"] = total_lines_llm
            json_format_human["lines_missed"] = lines_missed_human
            json_format_human["total_lines"] = total_lines_human
            os.makedirs(llm_path, exist_ok=True)
            os.makedirs(human_path, exist_ok=True)
            try:
                with open(os.path.join(llm_path, project_name + ".json"), "w") as f:
                    json.dump(json_format_llm, f)
                with open(os.path.join(human_path, project_name + ".json"), "w") as f:
                    json.dump(json_format_human, f)
                
                print(f"results for data run {counter} were read and saved\n")
            except Exception as e:
                print(f"Failed to write to {project_name}.json: {e}")

def calc_compile_errors_over_runs(projects: List[Dict], num_of_runs: int, list_of_compile_errors: List[str], output_path: str):
    compile_error_counts = {error: [] for error in list_of_compile_errors}
    compile_error_counts["Other Category"] = []
    compile_error_stats = {}

    for run in range(1, num_of_runs + 1):
        run_errors = {error: 0 for error in list_of_compile_errors}
        run_errors["Other Category"] = 0
        for project in projects:
            for module in project[f"run_{run}"]["modules"]:
                if not module["could_not_be_compiled"]:
                    continue
                compile_erros = module.get("compile_errors", [])
                for error in compile_erros:
                    if error in run_errors.keys():
                        run_errors[error] += 1
                    else:
                        run_errors["Other Category"] += 1

        for error in list_of_compile_errors:
            compile_error_counts[error].append(run_errors[error])
        
        compile_error_counts["Other Category"].append(run_errors["Other Category"])
    
    # Calculate statistics for each compile error
    for error in list_of_compile_errors:
        compile_error_stats[f"{error}_total"] = sum(compile_error_counts[error])
        compile_error_stats[f"{error}_mean"] = statistics.mean(compile_error_counts[error])
        compile_error_stats[f"{error}_std"] = statistics.stdev(compile_error_counts[error])

    compile_error_stats["Other Category_total"] = sum(compile_error_counts["Other Category"])
    compile_error_stats["Other Category_mean"] = statistics.mean(compile_error_counts["Other Category"])
    compile_error_stats["Other Category_std"] = statistics.stdev(compile_error_counts["Other Category"])

    compile_error_stats = sorted(compile_error_stats.items(), key=lambda x: x[1], reverse=True)

    os.makedirs(output_path, exist_ok=True)
    utils.write_json(compile_error_counts, os.path.join(output_path, "compile_errors.json"))
    utils.write_json(compile_error_stats, os.path.join(output_path, "compile_errors_stats.json"))

def calc_execution_errors_over_runs(projects: List[Dict], num_of_runs: int, output_path: str):
    execution_error_counts = {}
    execution_errors_stats = {}

    for run in range(1, num_of_runs + 1):
        run_errors = {}
        for project in projects:
            for module in project[f"run_{run}"]["modules"]:
                if module["could_not_be_compiled"]:
                    continue
                if module["could_not_be_executed"]:
                    continue
                for result in module["benchmark_results"]:
                    if not result["is_executed_successfully"]:
                        if result["error"] in run_errors.keys():
                            run_errors[result["error"]] += 1
                        else:
                            run_errors[result["error"]] = 1

        for error in run_errors:
            if error in execution_error_counts.keys():
                execution_error_counts[error].append(run_errors[error])
            else:
                execution_error_counts[error] = [run_errors[error]]

    # Calculate statistics for each execution error
    for error in list(execution_error_counts.keys()):
        if len(execution_error_counts[error]) > 1:
            execution_errors_stats[f"{error}_total"] = sum(execution_error_counts[error])
            execution_errors_stats[f"{error}_mean"] = statistics.mean(execution_error_counts[error])
            execution_errors_stats[f"{error}_std"] = statistics.stdev(execution_error_counts[error])
    
    execution_errors_stats = sorted(execution_errors_stats.items(), key=lambda x: x[1], reverse=True)

    os.makedirs(output_path, exist_ok=True)
    utils.write_json(execution_errors_stats, os.path.join(output_path, "execution_errors_stats.json"))
    utils.write_json(execution_error_counts, os.path.join(output_path, "execution_error_counts.json"))

def calc_coverage_over_runs(project_names: List[str], output_path: str, 
                            data_run_paths: List[str], coverage_save_path: str, llm_save_path: str, human_save_path: str):
    coverage_analysis = []

    for project_name in project_names:
        project_coverage = {
            "name": project_name,
            "coverage_percentage_llm": [],
            "coverage_percentage_human": []
        }
        for data_run_path in data_run_paths:
            coverage_llm = utils.read_json(os.path.join(data_run_path, coverage_save_path, project_name, llm_save_path, project_name + ".json"))
            coverage_human = utils.read_json(os.path.join(data_run_path, coverage_save_path, project_name, human_save_path, project_name + ".json"))
            llm_coverage_percentage = ((coverage_llm["total_lines"] - coverage_llm["lines_missed"]) / coverage_llm["total_lines"]) * 100
            llm_coverage_percentage = round(llm_coverage_percentage, 2)
            human_coverage_percentage = ((coverage_human["total_lines"] - coverage_human["lines_missed"]) / coverage_human["total_lines"]) * 100
            human_coverage_percentage = round(human_coverage_percentage, 2)
            project_coverage["coverage_percentage_llm"].append(llm_coverage_percentage)
            project_coverage["coverage_percentage_human"].append(human_coverage_percentage)
        
        # calculate coverage stat
        project_coverage["coverage_percentage_llm_mean"] = statistics.mean(project_coverage["coverage_percentage_llm"])
        project_coverage["coverage_percentage_llm_std"] = statistics.stdev(project_coverage["coverage_percentage_llm"])
        project_coverage["coverage_percentage_human_mean"] = statistics.mean(project_coverage["coverage_percentage_human"])
        project_coverage["coverage_percentage_human_std"] = statistics.stdev(project_coverage["coverage_percentage_human"])

        coverage_analysis.append(project_coverage)

    os.makedirs(output_path, exist_ok=True)
    utils.write_json(coverage_analysis, os.path.join(output_path, "coverage_analysis.json"))

    return coverage_analysis

def draw_box_plots(coverage_for_projects: List[Dict], output_path: str):
    data = []
    labels = []
    colors = []

    for project in coverage_for_projects:
        coverage_percentage_llm = project["coverage_percentage_llm"]
        coverage_percentage_human = project["coverage_percentage_human"]

        data.append(coverage_percentage_llm)
        labels.append(f"{project['name']} (LLM_Generated)")
        colors.append("blue")

        data.append(coverage_percentage_human)
        labels.append(f"{project['name']} (Human_Generated)")
        colors.append("green")

    # Create the plot
    plt.figure(figsize=(10, 6))
    box = plt.boxplot(data, patch_artist=True)

    # Color the boxes
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)

    plt.xticks(range(1, len(labels) + 1), labels, rotation=30, ha='right')
    plt.ylabel('Coverage Percentage')
    plt.title('Line Coverage Comparison: LLM vs Human JMH Microbenchmarks')
    plt.grid(True)
    plt.tight_layout()

    # Save the plot
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(os.path.join(output_path, "box_plot.png"))
    plt.close()

def read_coverage_values_from_user(prompt: str):
    print(prompt)
    lines_missed = int(input("Enter the number of lines missed: "))
    total_lines = int(input("Enter the total number of lines: "))
    return lines_missed, total_lines