"""
main.py holds all of the pipelines in order and executes them from beginning to the end as
they are intended, which consist of three main steps of : setup, generate, analyze

"""

from setup import setup
from generate import generate_benchmarks
from analysis import setup_configs
from utils import read_json
from pathlib import Path


project_data = read_json(Path("./src/projects.json").resolve())

# TODO: replace the model_url and model_name with envioronment variables or config files variables
project_data = setup(
    model_url="http://127.0.0.1:11434", model_name="mistral", project_data=project_data
)

# Example of 10 modules only first project
project_data['projects'][3]['modules'] = project_data['projects'][3]['modules'][0:10]
project_data['projects'] = [project_data['projects'][3]]

benchmarks = generate_benchmarks(project_data, model_name="mistral")

setup_configs(project_data)