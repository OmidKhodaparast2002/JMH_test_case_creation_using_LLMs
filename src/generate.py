from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

######################### DELETE THESE IMPORTS #############################
from utils import read_json
from setup import setup

############################################################################

output_schema = {
    "title": "JMH Benchmark",
    "type": "object",
    "properties": {
        "Benchmark_code": {
            "type": "string",
            "description": "The generated benchmark code for the given module using the JMH framework",
        },
    },
    "required": ["Benchmark code"],
}


def prompt_llm(template: object, module_data: object) -> dict:
    # Initialize a chatbot with structured output
    llm = ChatOllama(
        model="gemma:2b"
    )  # TODO : refactor the model name it should come from a config file
    # TODO: Move the initialization to the generate benchamrk function to avoid reinitializing
    llm = llm.with_structured_output(output_schema)

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
        {"module": [HumanMessage(content=f"Java Module Code:\n{module_data['code']}")]}
    )

    response = {
        "mod_name": module_data["mod_name"],
        "Benchmark_code": llm_response["Benchmark_code"],
    }

    return response


def check_output(llm_output: object, dest: Path) -> object:
    """
    This function checks the output of the LLM and validate its format and then writes the
    created JMH becnhmark to the given destination folder

    Args:
        llm_output (object): given output by LLM which is expected in the JMH_Benchmark class
        format

        dest (Path): given destination path for the module that JMH benchmarks need to be stored in.

    Returns:
        object: returns an object {"dest": "path"} which returns the destination to the module

    """
    # TODO: Implement the function
    # validate the received output
    # if it is not valid raise an error
    # if it is valid write it to the destination folder with format of .java

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

    inputs = (
        []
    )  # project name [{"project_name", content:[{"module_path": "code", ...}] }, ...]

    for project in project_data["projects"]:

        current_input = {"project_name": project["name"], "content": []}

        for mod in project[
            "modules"
        ]:  # mod is a string representing the path to a module
            code = load_code(Path(mod))  # read the code of the given module

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
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return code
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def generate_benchmarks(project_data: dict):  # complete pipe line
    project_modules = load_input(project_data)
    prompt_template = read_json(Path("./src/prompt.json"))
    print(prompt_template)

    outputs = (
        []
    )  # [{'project_name', 'benchmarks': [{'mod_name', 'benchmark_path'}, ...]}]

    for p in project_modules:  # for each project

        current_output = {"project_name": p["project_name"], "benchmarks": []}

        for module in p["content"]:  # for each module in the project
            response = prompt_llm(prompt_template, module)
            benchmark_path = check_output(response, Path("./output"))

            # create pair of mod_name (path to the original module) and benchmark_path (path to the respective benchmark of the module)
            current_output["benchmarks"].append(
                {"mod_name": module["mod_name"], "benchmark_path": benchmark_path}
            )

        outputs.append(current_output)
    return outputs


# Example usage
if __name__ == "__main__":
    # generate()
    project_data = read_json(Path("./src/projects.json").resolve())

    prompt_template = read_json(Path("./src/prompt.json"))

    project_data = setup(
        model_url="http://127.0.0.1:11434",
        model_name="gemma:2b",
        project_data=project_data,
    )

    llm_input = load_input(project_data)
    response = prompt_llm(prompt_template, llm_input[0]["content"][12])
    print(response)
    # code = load_code(Path("/home/amirpooya78/thesis/JMH_test_case_creation_using_LLMs/projects/gson/gson/src/main/java/com/google/gson/ExclusionStrategy.java"))
    # print(code)
