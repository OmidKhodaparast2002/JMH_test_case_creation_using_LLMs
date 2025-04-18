import re
import os

import javalang
import re

def remove_non_public_methods_regex(code: str) -> str:
    # Remove method bodies for private, protected, and package-level methods
    method_pattern = re.compile(
        r'(?:@\w+\s*)*'                                     # Optional annotations
        r'(?:(?:private|protected)\s+|(?<!public\s))'       # private/protected or no 'public'
        r'(?:[\w<>\[\]]+\s+)+'                              # return type
        r'\w+\s*\([^)]*\)\s*'                               # method name + args
        r'(?:throws\s+[\w\s,]+)?\s*'                         # optional throws
        r'\{(?:[^{}]*|\{[^{}]*\})*\}',                      # method body
        re.DOTALL
    )
    return method_pattern.sub('', code)


def remove_non_public_methods(code: str) -> str:
    try:
        tree = javalang.parse.parse(code)
    except (javalang.parser.JavaSyntaxError,
            javalang.tokenizer.LexerError,
            UnicodeDecodeError,
            IndexError,
            AttributeError) as e:
        print(f"[WARN] javalang failed to parse Java file. Returning code as is. Reason: {e}")
        return code

    lines = code.splitlines()
    lines_to_remove = set()

    for _, node in tree:
        if isinstance(node, javalang.tree.MethodDeclaration) and node.position:
            if 'public' not in node.modifiers:
                start = node.position.line - 1
                brace_count = 0
                end = start
                while end < len(lines):
                    brace_count += lines[end].count('{') - lines[end].count('}')
                    end += 1
                    if brace_count <= 0 and '{' in lines[start]:
                        break
                for i in range(start, end):
                    lines_to_remove.add(i)

    return '\n'.join(line for i, line in enumerate(lines) if i not in lines_to_remove)


def contains_interface_or_abstract_class(code):
    return bool(re.search(r'\binterface\b', code)) or bool(re.search(r'\babstract\s+class\b', code))

def run_analysis(project_obj, modules_path):
    counter = 0
    for root, dirs, files in os.walk(modules_path):
        for file in files:
            counter += 1
            print(f"Running static analysis file number {counter}...")
            if file.endswith(".java"):
                with open(os.path.join(root, file), "r") as f:
                    code = f.read()
                    # Remove comments
                    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
                    code = re.sub(r'//.*', '', code)

                    if contains_interface_or_abstract_class(code):
                        continue  # Skip this module

                    code = remove_non_public_methods(code)

                module = {
                    "name": file,
                    "path": os.path.join(root, file),
                    "code": code
                }
                project_obj["modules"].append(module)

def run_analysis_on_projects(projects):
    for project in projects:
        print(f"Running static analysis on {project['name']}...")
        run_analysis(project, project["analysis_path"])
