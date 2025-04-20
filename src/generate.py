from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from utils import read_json
import shutil
import re

######################### DELETE THESE IMPORTS #############################
from setup import setup

############################################################################

output_schema = {
    "title": "JMH Benchmark",
    "type": "object",
    "properties": {
        "benchmark_code": {
            "type": "string",
            "description": "The generated java microbenchmark for the given module using the JMH framework",
        },
        "class_name": {
            "type": "string",
            "description": "The name of the generated Java class.",
        },
    },
    "required": ["benchmark_code", "class_name"],
}


def prompt_llm(llm, template: object, module_data: object) -> dict:
    # construct the prompt template
    prompt = ChatPromptTemplate(
        [
            ("system", template["system"]),
            ("user", template["user"]),
            MessagesPlaceholder(
                "module"
            ),  # placeholder that will be filled with java code
        ]
    )

    # chain prompt model and fromat output together
    chain = prompt | llm

    # invoke the model for response
    llm_response = chain.invoke(
        {"module": [HumanMessage(content=f"Java Module:\n{module_data['code']}")]}
    )

    response = {
        "mod_name": module_data["mod_name"],
        "benchmark_code": llm_response["benchmark_code"],
        "class_name": llm_response["class_name"],
    }

    return response


def save_llm_output(llm_output: object, dest: Path) -> str:
    """
    This function checks the output of the LLM and then writes the
    created JMH becnhmark to the given destination folder

    Args:
        llm_output (object): given output by LLM which is expected in the JMH_Benchmark class
        format

        dest (Path): given destination path for the module that JMH benchmarks need to be stored in.

    Returns:
        object: returns a string representing the path to the saved benchmark paht/file.java

    """
    benchmark_code = llm_output["benchmark_code"]
    class_name = llm_output["class_name"]

    # Ensure the destination directory exists
    dest.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

    # Construct the full file path
    jmh_file = dest / f"{class_name}.java"

    with open(jmh_file, "w") as file:
        file.write(benchmark_code)

    return str(jmh_file)


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

    inputs = (
        []
    )  # project name [{"project_name", content:[{"module_path": "code", ...}] }, ...]

    for project in project_data["projects"]:

        current_input = {"project_name": project["name"], "content": []}

        for mod in project[
            "modules"
        ]:  # mod is a string representing the path to a module
            code = load_code(Path(mod))  # read the code of the given module
            # Skip if it's an interface, abstract class, or has no methods
            if is_skippable(code):
                continue
            # Add the module name alongside its code to the content of the project (current input)
            current_input["content"].append({"mod_name": mod, "code": code})

        # Add the project object to the inputs
        inputs.append(current_input)

    return inputs

def is_skippable(code: str) -> bool:
    """
    Returns True if the Java code is an interface, an abstract class, or doesn't contain any methods.
    """
    if "interface" in code:
        return True
    if "abstract class" in code:
        return True
    # Match method declarations: e.g., public void foo(), int bar(), etc.
    method_pattern = re.compile(r"\b(public|private|protected)?\s+[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*{")
    if not method_pattern.search(code):
        return True
    return False

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
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return code
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def generate_benchmarks(project_data: dict, model_name: str):  # complete pipe line
    project_modules = load_input(project_data)
    prompt_template = read_json(Path("./src/prompt.json"))

    # Initialize chat model
    llm = ChatOllama(model=model_name)
    llm = llm.with_structured_output(output_schema)

    outputs = (
        []
    )  # [{'project_name', 'benchmarks': [{'mod_name', 'benchmark_path'}, ...]}]

    for p in project_modules:  # for each project
        project_info = next(
            proj
            for proj in project_data["projects"]
            if proj["name"] == p["project_name"]
        )

        benchmarks_folder = Path(project_info.get("llm_benchmarks_path"))
        print("Creating benchmarks...")
        print(benchmarks_folder)

        # 🧹 Clean the benchmarks folder before starting
        if benchmarks_folder.exists() and benchmarks_folder.is_dir():
            for file in benchmarks_folder.iterdir():
                try:
                    if file.is_file() or file.is_symlink():
                        file.unlink()
                    elif file.is_dir():
                        shutil.rmtree(file)
                except Exception as e:
                    print(f"Failed to delete {file}: {e}")
        else:
            benchmarks_folder.mkdir(parents=True, exist_ok=True)

        current_output = {"project_name": p["project_name"], "benchmarks": []}

        for module in p["content"]:  # for each module in the project

            response = prompt_llm(llm, prompt_template, module)  # generate a benchmark

            benchmark_path = save_llm_output(
                response, benchmarks_folder
            )  # store the benchmark

            # create pair of mod_name (path to the original module) and benchmark_path (path to the respective benchmark of the module)
            current_output["benchmarks"].append(
                {"mod_name": module["mod_name"], "benchmark_path": benchmark_path}
            )

        outputs.append(current_output)
    return outputs


# Example usage
if __name__ == "__main__":

    project_data = read_json(Path("./src/projects.json").resolve())

    # prompt_template = read_json(Path("./src/prompt.json"))

    project_data = setup(
        model_url="http://127.0.0.1:11434",
        model_name="mistral",
        project_data=project_data,
    )

    outputs = generate_benchmarks(project_data)

    """
    llm_input = load_input(project_data)
    response = prompt_llm(prompt_template, llm_input[0]["content"][12])
    print(response["class_name"])
    print(response["benchmark_code"])
    """
