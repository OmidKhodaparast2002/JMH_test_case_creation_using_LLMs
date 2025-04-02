import os
import json

def folder_exists(folder_path):
    return os.path.exists(folder_path)

def create_folder(folder_path):
    os.makedirs(folder_path)

def write_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
