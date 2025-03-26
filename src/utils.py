import subprocess
import os
import json
import requests

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

def prompt_llm(prompt, api_key):
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

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    response_message = response.json()["choices"][0]["message"]["content"]

    print(response_message)

    print("\n\n\n\n")

    if "```java" in response_message:
        code = response_message.split("```java")[1].split("```")[0]
        print(code)
        return code
    else:
        raise Exception("No code found in response")


