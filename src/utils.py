import subprocess
import os
import json
import requests
import time
import re
import xml.etree.ElementTree as ET

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
                    # Remove comments
                    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
                    code = re.sub(r'//.*', '', code)
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
                    raise NoCodeFoundError("No code found in response")

            elif response.status_code == 429:
                print(response.text)
                print("\n\nRate limit hit. Waiting and retrying...")
                time.sleep(60)
            else:
                print("Error from API:", response.status_code, response.text)
                raise APIError("API Error")

    raise Exception("Max retries exceeded")

def configure_pom(parent_pom_path, child_pom_str, child_pom_insert_path):
    xmlns = "http://maven.apache.org/POM/4.0.0"
    namespace = f"{{{xmlns}}}"

    parent_tree = ET.parse(parent_pom_path)
    parent_root = parent_tree.getroot()

    child_root = ET.fromstring(child_pom_str)

    if parent_root is None:
        raise Exception("Failed to parse parent POM")

    parent_group_id = parent_root.find(namespace + "groupId")
    parent_artifact_id = parent_root.find(namespace + "artifactId")
    parent_version = parent_root.find(namespace + "version")

    if parent_group_id is None or parent_artifact_id is None or parent_version is None:
        raise Exception("Failed to find groupId, artifactId, or version in parent POM")

    if child_root is None:
        raise Exception("Failed to parse child POM")

    # Add parent tag as child of root, i.e. project
    child_parent_el = ET.SubElement(child_root, namespace + "parent")
    child_parent_groupId_el = ET.SubElement(child_parent_el, namespace + "groupId")
    child_parent_groupId_el.text = parent_group_id.text
    child_parent_artifactId_el = ET.SubElement(child_parent_el, namespace + "artifactId")
    child_parent_artifactId_el.text = parent_artifact_id.text
    child_parent_version_el = ET.SubElement(child_parent_el, namespace + "version")
    child_parent_version_el.text = parent_version.text

    # Add parent as dependency to child
    child_dependencies_el = child_root.find(namespace + "dependencies")
    if child_dependencies_el is None:
        child_dependencies_el = ET.SubElement(child_root, namespace + "dependencies")

    child_dependency_el = ET.SubElement(child_dependencies_el, namespace + "dependency")
    child_dependency_groupId_el = ET.SubElement(child_dependency_el, namespace + "groupId")
    child_dependency_groupId_el.text = parent_group_id.text
    child_dependency_artifactId_el = ET.SubElement(child_dependency_el, namespace + "artifactId")
    child_dependency_artifactId_el.text = parent_artifact_id.text
    child_dependency_version_el = ET.SubElement(child_dependency_el, namespace + "version")
    child_dependency_version_el.text = parent_version.text

    child_artifactId_el = child_root.find(namespace + "artifactId")
    if child_artifactId_el is None:
        raise Exception("Failed to find artifactId in child POM")
    
    # Add child to modules in parent
    parent_modules_el = parent_root.find(namespace + "modules")
    if parent_modules_el is None:
        parent_modules_el = ET.SubElement(parent_root, namespace + "modules")

    if not any(mod.text == child_artifactId_el.text for mod in parent_modules_el.findall(namespace + "module")):
        child_module_el = ET.SubElement(parent_modules_el, namespace + "module")
        child_module_el.text = child_artifactId_el.text

    ET.indent(parent_root, space="  ")
    ET.indent(child_root, space="  ")

    # Write parent changes back to file
    parent_tree.write(parent_pom_path, encoding="utf-8", xml_declaration=True)

    # Write child pom to the given path
    try:
        with open(child_pom_insert_path, "w", encoding="utf-8") as f:
            f.write(ET.tostring(child_root, encoding='utf-8', method='xml').decode('utf-8'))
    except Exception as e:
        print("Failed to write child POM to file:", e)

    return True

class APIError(Exception):
    pass

class NoCodeFoundError(Exception):
    pass