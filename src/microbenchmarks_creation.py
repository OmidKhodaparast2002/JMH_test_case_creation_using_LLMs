import requests
import time
import os

REQUEST_LIMIT_PER_MINUTE = 1000
TOKEN_LIMIT_PER_MINUTE = 250000
SECONDS_PER_MINUTE = 60
CHARS_PER_TOKEN = 4

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

    if response.status_code == 200:
        response_message = response.json()["choices"][0]["message"]["content"]

        if "```java" in response_message:
            code = response_message.split("```java")[1].split("```")[0]
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

class APIError(Exception):
    pass

class NoCodeFoundError(Exception):
    pass

class RateLimitError(Exception):
    pass

def create_microbenchmarks(projects, prompt_str, api_key):
    curr_timestamp = time.time()
    requests = 0

    for project in projects:
        tokens = 0
        i = 0
        save_path = project["microbenchmarks_path"]

        while i < len(project["modules"]):
            module = project["modules"][i]
            prompt = prompt_str + module["code"]

            if time.time() - curr_timestamp > SECONDS_PER_MINUTE:
                curr_timestamp = time.time()

            requests += 1
            tokens = len(prompt) // CHARS_PER_TOKEN + tokens 

            if tokens > TOKEN_LIMIT_PER_MINUTE and time.time() - curr_timestamp < SECONDS_PER_MINUTE:
                print("TPM exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                tokens = 0

            if requests > REQUEST_LIMIT_PER_MINUTE and time.time() - curr_timestamp < SECONDS_PER_MINUTE:
                print("RPM exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                requests = 0

            try:
                test = prompt_llm(prompt, api_key)
                module["test_code"] = test

                try:
                    with open(os.path.join(save_path, module["name"]), "w", encoding="utf-8") as f:
                        f.write(test)
                except Exception as e:
                    print("Error saving code:\n", e)
            except RateLimitError as e:
                print(e)
                time.sleep(60)
                i -= 1

            except NoCodeFoundError as e:
                print(e)
                module["test_code"] = "Code not found"

            except APIError as e:
                print(e)
                module["test_code"] = "API error"

            except Exception as e:
                print(e)
                module["test_code"] = "Error"

            i += 1