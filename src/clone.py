import utils
import subprocess
import os

def clone(ssh_str, folder_path):
    try:
        subprocess.run(["git", "clone", ssh_str], cwd=folder_path)
    except Exception as e:
        print(e)
        print(f"Failed to clone {ssh_str}")
        exit(1)

def clone_projects(path_to_clone, projects, generated_jmh_dir):
    if not utils.folder_exists(path_to_clone):
        utils.create_folder(path_to_clone)
        for project in projects:
            clone(project["ssh_url"], path_to_clone)
            print("Checking out to the stable snap shot")
            checkout_to_correct_snap_shot(project["root_path"], project["snap_shot_commit"])
    else:
        utils.remove_last_run_config(path_to_clone, generated_jmh_dir)

def checkout_to_correct_snap_shot(project_root_path, snapshot):
    try:
        subprocess.run(["git", "checkout", snapshot], cwd=project_root_path)
    except Exception as e:
        print(e)
        print(f"Failed to checkout to {snapshot}")
        exit(1)
