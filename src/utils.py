import os
import json
import re

def folder_exists(folder_path):
    return os.path.exists(folder_path)

def create_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)

def write_json(data, path):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to write to {path}: {e}")

def read_projects(path, project_names):
    projects = []
    
    for project_name in project_names:
        project_path = os.path.join(path, project_name + ".json")
        try:
            with open(project_path, "r") as f:
                project = json.load(f)
                projects.append(project)
        except Exception as e:
            print(f"Failed to read {project_path}: {e}")

    return projects

def is_test_code_without_jmh(tes_code):

    tes_code = tes_code.strip().lower()

    # Skip if no code was generated
    if not tes_code:
        return True
    
    # Remove multiline and single-line comments
    code_cleaned = re.sub(r"/\*.*?\*/", "", tes_code, flags=re.DOTALL)
    code_cleaned = re.sub(r"//.*", "", code_cleaned).strip()

    # If nothing remains after removing comments
    if not code_cleaned:
        return True

    return False
