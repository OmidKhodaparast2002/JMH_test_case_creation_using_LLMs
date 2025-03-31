import utils
from dotenv import load_dotenv
import os
import time

load_dotenv()

GPT_KEY = os.getenv("GPT_KEY")

PROJECT_INFO = [
    {
        "name": "logging-log4j2",
        "ssh_url": "git@github.com:apache/logging-log4j2.git",
        "analysis_path": "../projects/logging-log4j2/log4j-core/src/main/java/org/apache/logging/log4j/core",
        "modules": []
    },
    {
        "name": "kafka",
        "ssh_url": "git@github.com:apache/kafka.git",
        "analysis_path": "../projects/kafka/core/src/main/java/kafka/server",
        "modules": []
    },
    {
        "name": "RxJava",
        "ssh_url": "git@github.com:ReactiveX/RxJava.git",
        "analysis_path": "../projects/RxJava/src/main/java/io/reactivex/rxjava3",
        "modules": []
    },
    {
        "name": "Java",
        "ssh_url": "git@github.com:TheAlgorithms/Java.git",
        "analysis_path": "../projects/Java/src/main/java/com/thealgorithms",
        "modules": []
    },
    {
        "name": "gson",
        "ssh_url": "git@github.com:google/gson.git",
        "analysis_path": "../projects/gson/gson/src/main/java/com/google/gson",
        "modules": []
    },
    {
        "name": "jjwt",
        "ssh_url": "git@github.com:jwtk/jjwt.git",
        "analysis_path": "../projects/jjwt/impl/src/main/java/io/jsonwebtoken/impl",
        "modules": []
    }
]

PROJECTS_PATH = "../projects"
DATA_COLLECTION_PATH = "../data/collected"

MAX_RETRIES = 5

PROMPT_TEXT_ONE = """You are a senior verification developer. You are an expert in
writing JMH microbenchmark test cases. You are also an expert analyzing code and writing JMH test cases for it.
You are proficient in the Java programming language. You are assigned to write an appropriate
number of JMH microbenchmark test cases to test the performance of the following code module. Please only provide the the benchmark module
and no explanations. You must ignore "Abstract classes" and "Interfaces":\n\n"""

def main():
    if not utils.folder_exists(PROJECTS_PATH):
        utils.create_folder(PROJECTS_PATH)
        for project in PROJECT_INFO:
            utils.clone(project["ssh_url"], PROJECTS_PATH)

    for project in PROJECT_INFO:
        utils.run_analysis(project, project["analysis_path"])
    
    for project in PROJECT_INFO:
        tokens = 0
        for module in project["modules"]:
            print(f"tokens used: {tokens}")
            prompt = PROMPT_TEXT_ONE + module["code"]
            tokens = len(prompt) // 4 + tokens
            if tokens > 6000:
                time.sleep(60)
                tokens = 0
            try:
                tests = utils.prompt_llm(prompt, GPT_KEY, MAX_RETRIES)
                module["test_code"] = tests
            except utils.APIError as e:
                print(e)
                module["test_code"] = "public static void main(String[] args) {throw new Exception(\"Failed to generate tests\");}"
            except Exception as e:
                print(e)
                module["test_code"] = "public static void main(String[] args) {throw new Exception(\"Module is not testable\");}"
        break
    
    for project in PROJECT_INFO:
        if not utils.folder_exists(DATA_COLLECTION_PATH):
            utils.create_folder(DATA_COLLECTION_PATH)
        utils.write_json(project, f"{DATA_COLLECTION_PATH}/{project['name']}.json")
            

if __name__ == "__main__":
    main()