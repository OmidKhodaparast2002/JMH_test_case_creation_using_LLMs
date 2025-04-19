import requests
import time
import os
import utils

REQUEST_LIMIT_PER_MINUTE = 1000
TOKEN_LIMIT_PER_MINUTE = 250000
SECONDS_PER_MINUTE = 60
CHARS_PER_TOKEN = 4

def prompt_llm(prompt, api_key, interface_found_str, abstract_found_str):
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

    if response.status_code == 200:
        response_message = response.json()["choices"][0]["message"]["content"]

        if "```java" in response_message:
            code = response_message.split("```java")[1].split("```")[0]
            if utils.is_test_code_without_jmh(code):
                raise NoCodeFoundError("No code found in response")
            return code
        else:
            raise NoCodeFoundError("No code found in response")
        
    elif response.status_code == 429:
        print(response.text)
        print("Rate limit hit. Waiting and retrying...")
        RateLimitError("Rate limit hit")

    else:
        print("Error from API:", response.status_code, response.text)
        raise APIError("API Error")

def create_microbenchmarks(projects, prompt_str, api_key, interface_found_str, abstract_found_str, no_code_found_str, api_error_str, unknown_error_str, max_retries):
    curr_timestamp = time.time()
    requests = 0
    api_retries = 0
    no_code_retries = 0

    for project in projects:
        print(f"creating microbenchmarks for {project['name']}...")
        tokens = 0
        i = 0

        print(f"Creating microbenchmarks for {project['name']}...")

        while i < len(project["modules"]):
            print(f"creating microbenchmark number {i} out of {len(project['modules'])}...")
            module = project["modules"][i]
            prompt = prompt_str + module["code"]

            if time.time() - curr_timestamp > SECONDS_PER_MINUTE:
                curr_timestamp = time.time()

            requests += 1
            tokens = len(prompt) // CHARS_PER_TOKEN + tokens 

            if tokens > TOKEN_LIMIT_PER_MINUTE and time.time() - curr_timestamp < SECONDS_PER_MINUTE:
                print("TPM exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                print("Resuming...")
                requests = 0
                tokens = 0

            if requests > REQUEST_LIMIT_PER_MINUTE and time.time() - curr_timestamp < SECONDS_PER_MINUTE:
                print("RPM exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                print("Resuming...")
                tokens = 0
                requests = 0

            try:
                test = prompt_llm(prompt, api_key, interface_found_str, abstract_found_str)
                module["test_code"] = test
            except RateLimitError as e:
                print(e)
                time.sleep(60)
                continue

            except NoCodeFoundError as e:
                print(e)
                module["test_code"] = no_code_found_str
                if no_code_retries < max_retries:
                    no_code_retries += 1
                    print(f"Retrying {no_code_retries}/{max_retries}...")
                    continue
                else:
                    module["test_code"] = no_code_found_str
                    no_code_retries = 0

            except APIError as e:
                print(e)
                print(f"API error, retrying...")
                if api_retries < max_retries:
                    api_retries += 1
                    print(f"Retrying {api_retries}/{max_retries}...")
                    continue
                else:
                    module["test_code"] = api_error_str
                    api_retries = 0

            except Exception as e:
                print(e)
                module["test_code"] = unknown_error_str

            i += 1
            api_retries = 0
            no_code_retries = 0

class APIError(Exception):
    pass

class NoCodeFoundError(Exception):
    pass

class RateLimitError(Exception):
    pass