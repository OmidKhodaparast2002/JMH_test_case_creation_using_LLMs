import os
import json
import re
import shutil
import subprocess
from typing import List

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

def is_test_code_without_jmh(code):

    tes_code = code.strip().lower()

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

def remove_dir_and_files(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def remove_last_run_config(projects_path, generated_jmh_dir):
    if os.path.exists(projects_path):
        for dir in os.listdir(projects_path):
            dir_path = os.path.join(projects_path, dir)
            if os.path.isdir(dir_path):
                for dir2 in os.listdir(dir_path):
                    if dir2 == generated_jmh_dir:
                        shutil.rmtree(os.path.join(dir_path, dir2))

def remove_existing_package_statement(java_code: str) -> str:
    """
    Removes the first occurrence of a 'package' declaration in the Java code.
    """
    return re.sub(r'^\s*package\s+[\w\.]+;\s*', '', java_code, count=1, flags=re.MULTILINE)

def is_java_version_installed(java_version: str) -> bool:
    return os.path.exists(os.path.expanduser(f"~/.sdkman/candidates/java/{java_version}"))

def install_java_version(java_version: str):
    try:
        subprocess.run(
            f"bash -c 'source $HOME/.sdkman/bin/sdkman-init.sh && sdk install java {java_version} -y'",
            shell=True,
            executable="/bin/bash",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Java {java_version} using SDKMAN:\n{e.stderr}")
        raise e

def activate_java_version(java_version: str):
    try:
        subprocess.run(
            f"bash -c 'source $HOME/.sdkman/bin/sdkman-init.sh && sdk default java {java_version}'",
            shell=True,
            executable="/bin/bash",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # see if java -version works
        subprocess.run(["java", "-version"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to switch to Java {java_version} using SDKMAN:\n{e.stderr}")
        raise e

def extract_benchmark_names(java_source: str) -> List[str]:
    pattern = re.compile(
        r"@Benchmark\b.*?(?:public|protected|private)?\s+\w[\w<>\[\]]*\s+(\w+)\s*\(",
        re.DOTALL
    )
    return pattern.findall(java_source)
