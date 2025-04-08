from pathlib import Path

def prompt_llm(template: str, project_data:dict):
    return

def check_output():
    return

def load_input(project_data: dict) -> dict:
    
    return

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
    generate()

    #code = load_code(Path("/home/amirpooya78/thesis/JMH_test_case_creation_using_LLMs/projects/gson/gson/src/main/java/com/google/gson/ExclusionStrategy.java"))
    #print(code)
    