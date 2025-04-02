import re
import os

def run_analysis(project_obj, modules_path):
    for root, dirs, files in os.walk(modules_path):
        for file in files:
            if file.endswith(".java"):
                with open(os.path.join(root, file), "r") as f:
                    code = f.read()
                    # Remove comments
                    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
                    code = re.sub(r'//.*', '', code)
                module = {
                    "name": file,
                    "path": os.path.join(root, file),
                    "code": code
                }

                project_obj["modules"].append(module)

def run_analysis_on_projects(projects):
    for project in projects:
        run_analysis(project, project["analysis_path"])