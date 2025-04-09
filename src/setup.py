"""
setup.py module sets up all the necessary components before moving to the stage of prompting the
LLM and generating microbenchmarks.

Procedures included in setup.py:
 * Cloning selected projects for benchmark generation
 * Read the congigurations for anyalsis that extracts the necessary files for the becnhmarks
 * Creates a folder path for each project that only included necessary files for becnhmark generatoin
 * Sets up the LLM 

"""

import ollama
import requests
import json
from pathlib import Path
from typing import List
import subprocess
import os
import re
import json
from utils import read_json

def check_model_connectivity(model_url: str, model_name: str) -> bool:
    """
    Check if the given model is actually available and ready to generate output.

    Uses /api/generate with stream=false to confirm model is working.
    """
    try:
        url = f"{model_url}/api/generate"
        response = requests.post(url, json={
            "model": model_name,
            "prompt": "Hello",
            "stream": False
        })

        if response.status_code == 200:
            print("✅ Model is loaded and generating.")
            return True
        else:
            print(f"❌ Model returned unexpected status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error while checking model: {e}")
        return False


def clone_projects(project_data: dict, dest_folder: Path):
    """Clones a list of Git repositories to a destination folder.

    Args:
        proj_links: A list of Git repository URLs.
        dest_folder: The destination directory where repositories should be cloned.
    """

    # If the destination folder does not exist we create it otherwise it will be left as it is.
    os.makedirs(dest_folder, exist_ok=True) 

    project_urls = [project["ssh_url"] for project in project_data["projects"]]

    try:
        for url in project_urls:
            # Extract the repository name from the URL and wrapping it inside a Path object.
            repo_name = Path(re.search(r"/([^/]+?)(?:\.git)?$", url).group(1)) # regex to get repo name
            
            # Add the repo path to the repos folder.
            repo_path = dest_folder / repo_name

            # if repo exists skip cloning.
            if(os.path.isdir(repo_path)):
                continue

            subprocess.run(['git', 'clone', url, repo_path]) # Cloning into the repo folder

        print("All projects were cloned successfully.")
    except FileNotFoundError as exc: 
        print(f"Process failed because the executable could not be found.\n{exc}")
        exit(1)
    except subprocess.CalledProcessError as exc:
        print(
        f"Cloning failed because did not return a successful return code. "
        f"Returned {exc.returncode}\n{exc}"
        )
    except Exception as exc:
        print(f"An unexpected error occurred during cloning:\n{exc}")
        exit(1)



def prep_projects_modules(project_data: dict) -> dict:

    """
    This function finds all java files and fill the modules attribute of each project with
    paths to the java files inside in given analysis directory and subdirectories witihin it.

    Args:
        project_data: dict , project data coming from serialized json file

    Returns: 
        project_data: dict , filled modules attribute of each project with path of java files
        inside the anaylis path of the project
    """

    for project in project_data["projects"]:
        # Get the absolute path of each projest analysis path 
        analysis_path = Path(project["analysis_path"]).resolve()

        # check for if given analysis path is a valid directory
        if(os.path.isdir(analysis_path)):

            # recursively search for all java files in the analysis path
            java_files = list(analysis_path.rglob("*.java")) 

            # Save java files to modules attribute of each project
            project["modules"] = [str(f) for f in java_files] # stringify it for being a serializable json

            
        else:
            print(f"Given analysis path is not a directory for given project: {project['name']}")

    return project_data


def rmv_proj_comments(project_data: dict) -> dict:
    # Regex pattern to match single-line and multi-line comments
    comment_pattern = re.compile(
        r'//.*?$|/\*.*?\*/',
        re.DOTALL | re.MULTILINE
    )

    for project in project_data['projects']:

        file_paths = project['modules']

        for path in file_paths:
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    code = file.read()

                # Remove comments using regex
                cleaned_code = re.sub(comment_pattern, '', code)

                # Optionally, remove trailing whitespaces on each line
                cleaned_code = '\n'.join(line.rstrip() for line in cleaned_code.splitlines())

                # Write the cleaned code back to the file
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(cleaned_code)

                print(f"Cleaned comments from: {path}")
            except Exception as e:
                print(f"Failed to process {path}: {e}")

    return project_data



def setup(model_url:str, model_name:str, project_data:dict) -> dict:
    """
    setup pipeline includes all the steps that are needed to be taken before generation pipeline
    such as:
        * checking the connectivity to the LLM,
        * cloning the projects
        * Loading the modules path for each projects that will be used for JMH generation
        * clearing comments from the modules 
    """
    LLM_available = check_model_connectivity(model_url, model_name)

    if(not LLM_available):
        raise Exception(f'model: {model_name} {model_url} is not available')
    
    clone_projects(project_data, Path('./projects'))

    project_data = prep_projects_modules(project_data)

    project_data = rmv_proj_comments(project_data)

    return project_data


# Example usage
if __name__ == "__main__": 
    
    project_data = read_json(Path('./src/projects.json').resolve())

    project_data = setup(model_url='http://127.0.0.1:11434', model_name='gemma:2b', project_data=project_data)

