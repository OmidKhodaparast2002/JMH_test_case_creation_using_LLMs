"""
main.py holds all of the pipelines in order and executes them from beginning to the end as 
they are intended, which consist of three main steps of : setup, generate, analyze

"""

from setup import setup
from utils import read_json
from pathlib import Path

project_data = read_json(Path('./src/projects.json').resolve())

# TODO: replace the model_url and model_name with envioronment variables or config files variables
project_data = setup(model_url='http://127.0.0.1:11434', model_name='mistral', project_data=project_data)
