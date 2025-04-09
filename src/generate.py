from pathlib import Path


######################### DELETE THESE IMPORTS #############################
from utils import read_json
from setup import setup
############################################################################

def prompt_llm(template: str, project_data:dict):
    return

def check_output():
    return

def load_input(project_data: dict) -> list:
    """
    This function takes project_data JSON object created by the setup pipeline and creates
    an array of project objects with only project name and modules attributes

    Args:
        project_data (dict): format:
            {
            'projects':
                [
                    {
                        'name': 'project_name',
                            .
                            .
                            .
                        'modules': ['path to a java module in the project', ...]
                    }
                ]
            }
    
    Returns: 
        inputs (list): Format -> 
        [{'project_name': 'name', 'content': [ {'mod_name': '*.java', 'code': 'java_code'}, ... ] }, ...]

    """
    
    inputs = [] # project name [{"project_name", content:[{"module_path": "code", ...}] }, ...]

    for project in project_data['projects']:

        current_input = {"project_name": project["name"], "content": []}

        for mod in project["modules"]: # mod is a string representing the path to a module
            code = load_code(Path(mod)) # read the code of the given module

            # Add the module name alongside its code to the content of the project (current input)
            current_input["content"].append({"mod_name": mod, "code": code}) 

        # Add the project object to the inputs
        inputs.append(current_input)

    return inputs

def load_code(file_path: Path) -> str:
    """
    This function takes a path to a code file and reads its content.
    
    Args: 
        file_path (Path): The path object to the file

    Returns:
        str: Code content of the file as string

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be accessed due to permissions.
        IOError: If an I/O error occurs.
        ValueError: If the file path is not a file.
    """
    if not file_path.is_file():
        raise ValueError(f"The provided path is not a file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        return code
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def generate(): # complete pipe line 
    return


# Example usage
if __name__ == '__main__':
    #generate()
    project_data = read_json(Path('./src/projects.json').resolve())

    project_data = setup(model_url='http://127.0.0.1:11434', model_name='gemma:2b', project_data=project_data)

    llm_input = load_input(project_data)
    #code = load_code(Path("/home/amirpooya78/thesis/JMH_test_case_creation_using_LLMs/projects/gson/gson/src/main/java/com/google/gson/ExclusionStrategy.java"))
    #print(code)
    