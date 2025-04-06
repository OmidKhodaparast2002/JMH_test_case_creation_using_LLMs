import utils
import os
import subprocess
import re

def write_collected_data_in_json(projects, path):
    if not utils.folder_exists(path):
        utils.create_folder(path)
        
    for project in projects:
        utils.write_json(project, os.path.join(path, project["name"] + ".json"))

def compile_microbenchmarks_for_project(project, generated_microbenchmarks_dir, root_path, has_maven, abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str):
    abstract_classess = 0
    modules_with_no_generated_code = 0
    interfeces = 0
    modules_with_API_errors = 0
    modules_with_unknown_errors = 0
    modules_not_compiled = 0

    module_names_with_no_generated_code = []
    module_names_with_API_errors = []
    module_names_with_unknown_errors = []
    module_names_with_abstract_classes = []
    module_names_with_interfaces = []
    module_names_that_did_not_compile = []

    # Install all project before moving on
    if has_maven:
        try: 
            subprocess.run(
                ["mvn", "spotless:apply"],
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            subprocess.run(
                ["mvn", "clean", "install", "-DskipTests"],
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except Exception as e:
            print(f"Failed to install {project['name']} project: {e}")
            return

    for module in project["modules"]:

        if module["test_code"] == abstract_class_found_str:
            abstract_classess += 1
            module_names_with_abstract_classes.append(module["name"])
        elif module["test_code"] == interface_found_str:
            interfeces += 1
            module_names_with_interfaces.append(module["name"])
        elif module["test_code"] == no_code_found_str:
            modules_with_no_generated_code += 1
            module_names_with_no_generated_code.append(module["name"])

        elif module["test_code"] == api_error_str:
            modules_with_API_errors += 1
            module_names_with_API_errors.append(module["name"])
        elif module["test_code"] == unknown_error_str:
            modules_with_unknown_errors += 1
            module_names_with_unknown_errors.append(module["name"])
        else:
            try:
                # Extract class name from test code
                match = re.search(r'\bpublic\s+class\s+([A-Za-z_]\w*)', module["test_code"])
                if match:
                    class_name = match.group(1)
                else:
                    class_name = module["name"][0:len(module["name"]) - 5]  # or raise an error if needed

                with open(os.path.join(project["microbenchmarks_path"], class_name + ".java"), "w") as f:
                    f.write(module["test_code"])
            except Exception as e:
                print(f"Failed to write to {project['microbenchmarks_path']}: {e}")

            try:
                if has_maven:
                    subprocess.run(
                        ["mvn", "clean", "-B", "compile"],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    module["could_not_be_compiled"] = False
                else:
                    subprocess.run(
                        ["gradle", "build"],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    module["could_not_be_compiled"] = False
            except Exception as e:
                print(e.stderr)
                print(f"Failed to compile {os.path.join(project['microbenchmarks_path'], module['name'])}: {e}")
                modules_not_compiled += 1
                module_names_that_did_not_compile.append(module["name"])
                module["could_not_be_compiled"] = True
                module["error"] = extract_java_error_type(e.stderr)
                print(module["error"])
                module["full_error"] = e.stderr
            
            # delete the microbenchmark file
            try:
                os.remove(os.path.join(project["microbenchmarks_path"], module["name"]))
            except Exception as e:
                print(f"Failed to delete {project['microbenchmarks_path']}: {e}")

    project["modules_with_no_generated_code"] = modules_with_no_generated_code
    project["modules_with_API_errors"] = modules_with_API_errors
    project["modules_with_unknown_errors"] = modules_with_unknown_errors
    project["modules_with_abstract_classes"] = abstract_classess
    project["modules_with_interfaces"] = interfeces
    project["modules_not_compiled"] = modules_not_compiled

    project["module_names_with_no_generated_code"] = module_names_with_no_generated_code
    project["module_names_with_API_errors"] = module_names_with_API_errors
    project["module_names_with_unknown_errors"] = module_names_with_unknown_errors
    project["module_names_with_abstract_classes"] = module_names_with_abstract_classes
    project["module_names_with_interfaces"] = module_names_with_interfaces
    project["module_names_that_did_not_compile"] = module_names_that_did_not_compile


def compile_microbenchmarks_for_all_projects(projects, generated_microbenchmarks_dir, abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str):
    for project in projects:
        compile_microbenchmarks_for_project(project, generated_microbenchmarks_dir, project["root_path"], project["has_maven"], abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str)

def execute_compiled_microbenchmarks_for_project(project, generated_microbenchmarks_dir, root_path, has_maven, abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str):
    pass

def execute_compiled_microbenchmarks_for_all_projects(projects, generated_microbenchmarks_dir, abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str):
    for project in projects:
        execute_compiled_microbenchmarks_for_project(project, generated_microbenchmarks_dir, project["root_path"], project["has_maven"], abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str)

def extract_java_error_type(stderr_output):
    # 1. Prefer a meaningful [ERROR] line, skip the boilerplate
    for line in stderr_output.splitlines():
        if "[ERROR]" in line:
            # Strip prefix
            error = line.split("[ERROR]")[-1].strip()

            # Skip known unhelpful messages
        if error not in error.upper() or "COMPILATION FAILURE" not in error.upper() or "FAILED TO EXECUTE GOAL" not in error.upper():
                return error

    # 2. Fall back to lines with "error:"
    for line in stderr_output.splitlines():
        if "error:" in line.lower():
            return line.strip()

    # 3. Last resort
    return stderr_output.strip().splitlines()[0] if stderr_output else "UnknownError"
