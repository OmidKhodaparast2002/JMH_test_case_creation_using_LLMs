import utils
import os

def write_collected_data_in_json(projects, path):
    if not utils.folder_exists(path):
        utils.create_folder(path)
        
    for project in projects:
        utils.write_json(project, os.path.join(path, project["name"] + ".json"))