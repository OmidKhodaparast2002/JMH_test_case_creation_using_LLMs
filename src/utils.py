import subprocess
import os
import json
import requests
import time
from pathlib import Path

def folder_exists(folder_path):
    return os.path.exists(folder_path)

def create_folder(folder_path):
    os.makedirs(folder_path)

def clone(ssh_str, folder_path):
    subprocess.run(["git", "clone", ssh_str], cwd=folder_path)

def run_analysis(project_obj, path):
    for root, dirs, files in os.walk(project_obj["analysis_path"]):
        for file in files:
            if file.endswith(".java"):
                with open(os.path.join(root, file), "r") as f:
                    code = f.read()
                module = {
                    "name": file,
                    "path": os.path.join(root, file),
                    "code": code
                }

                project_obj["modules"].append(module)

def write_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def prompt_llm(prompt, api_key, max_retries):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(max_retries):
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

            if response.status_code == 200:
                response_message = response.json()["choices"][0]["message"]["content"]
                if "```java" in response_message:
                    code = response_message.split("```java")[1].split("```")[0]
                    return code
                else:
                    raise Exception("No code found in response")

            elif response.status_code == 429:
                print(response.text)
                print("\n\nRate limit hit. Waiting and retrying...")
                time.sleep(60)
            else:
                print("Error from API:", response.status_code, response.text)
                raise APIError("API Error")

    raise Exception("Max retries exceeded")


class APIError(Exception):
    pass


def read_json(path: Path):
    with open(path, 'r') as f:
        data = json.load(f)

    return data