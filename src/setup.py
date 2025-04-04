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

def check_model_connvectivity(model_url:str, model_name:str) -> bool:
    """
    This function checks the conncetivity to the LLM

    params:
        url: URL to the model

    returns:
        True (if model is available)
        False (if model is not available)
    """
    try:
        url = f"{model_url}/api/tags"
        
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        for model in data.get("models", []):
            if model["name"] == model_name:
                return True
                
        return False
    
    except requests.exceptions.RequestException as e:
        print(f"Error checking Ollama availability: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return False


def clone_projects(links, destination: Path):
    return

def load_projects(path):
    return


def rmv_proj_comments():
    return


def setup():
    return


# Example usage
if __name__ == "__main__": 
    check_model_connvectivity(model_url='http://127.0.0.1:11434', model_name='gemma:2b')