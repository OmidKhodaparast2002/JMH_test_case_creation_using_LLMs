import utils
import subprocess
import os

def clone(ssh_str, folder_path):
    subprocess.run(["git", "clone", ssh_str], cwd=folder_path)

def clone_projects(path_to_clone, projects):
    if not utils.folder_exists(path_to_clone):
        utils.create_folder(path_to_clone)
        for project in projects:
            clone(project["ssh_url"], path_to_clone)

