import utils
import os
import subprocess
import re

def write_collected_data_in_json(projects, path):
    if not utils.folder_exists(path):
        utils.create_folder(path)
        
    for project in projects:
        utils.write_json(project, os.path.join(path, project["name"] + ".json"))

def compile_microbenchmarks_for_project(project, generated_microbenchmarks_dir, root_path, has_maven, abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str):
    counter = 0
    
    abstract_classess = 0
    modules_with_no_generated_code = 0
    interfeces = 0
    modules_with_API_errors = 0
    modules_with_unknown_errors = 0
    modules_not_compiled = 0

    module_names_with_no_generated_code = []
    module_names_with_API_errors = []
    module_names_with_unknown_errors = []
    module_names_with_abstract_classes = []
    module_names_with_interfaces = []
    module_names_that_did_not_compile = []

    # Activate the Java version for this project
    if "java_version" in project:
        try:
            if not is_java_version_installed(project["java_version"]):
                install_java_version(project["java_version"])
            activate_java_version(project["java_version"])
        except Exception as e:
            print(f"Failed to activate Java version for {project['name']} project: {e}")
            return

    # Install all project before moving on
    if has_maven:
        try: 
            subprocess.run(
                ["mvn", "spotless:apply"],
                cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            subprocess.run(
                ["mvn", "clean", "install", "-DskipTests"],
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except Exception as e:
            print(f"Failed to install {project['name']} project: {e}")
            return

    for module in project["modules"]:
        counter += 1
        print(f"compiling microbenchmark number {counter} out of {len(project['modules'])}...")

        class_name = module["name"][0:len(module["name"]) - 5]

        if module["test_code"] == abstract_class_found_str:
            abstract_classess += 1
            module_names_with_abstract_classes.append(module["name"])
        elif module["test_code"] == interface_found_str:
            interfeces += 1
            module_names_with_interfaces.append(module["name"])
        elif module["test_code"] == no_code_found_str:
            modules_with_no_generated_code += 1
            module_names_with_no_generated_code.append(module["name"])

        elif module["test_code"] == api_error_str:
            modules_with_API_errors += 1
            module_names_with_API_errors.append(module["name"])
        elif module["test_code"] == unknown_error_str:
            modules_with_unknown_errors += 1
            module_names_with_unknown_errors.append(module["name"])
        else:
            try:
                # Extract class name from test code
                match = re.search(r'\bpublic\s+class\s+([A-Za-z_]\w*)', module["test_code"])
                if match:
                    class_name = match.group(1)

                with open(os.path.join(project["microbenchmarks_path"], class_name + ".java"), "w") as f:
                    f.write(module["test_code"])
            except Exception as e:
                print(f"Failed to write to {project['microbenchmarks_path']}: {e}")

            try:
                if has_maven:
                    subprocess.run(
                        ["mvn", "clean", "-B", "compile"],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    module["could_not_be_compiled"] = False
                else:
                    subprocess.run(
                        ["./gradlew", f":{generated_microbenchmarks_dir}:clean", f":{generated_microbenchmarks_dir}:compileJmhJava", "--info", "--no-daemon", "--rerun-tasks"],
                        cwd=root_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    module["could_not_be_compiled"] = False
            except subprocess.CalledProcessError as e:
                err = ''

                if project["has_maven"]:
                    err = e.stdout
                else:
                    err = e.stderr

                print(f"Failed to compile {os.path.join(project['microbenchmarks_path'], class_name + '.java')}.")

                modules_not_compiled += 1
                module_names_that_did_not_compile.append(module["name"])
                module["could_not_be_compiled"] = True

                module["compile_error"] = extract_java_error_type(err)
                print(module["error"], "\n\n")
                module["full_compile_error"] = err
            except Exception as e:
                err = str(e)

                print(f"Failed to compile {os.path.join(project['microbenchmarks_path'], class_name + '.java')}.")

                modules_not_compiled += 1
                module_names_that_did_not_compile.append(module["name"])
                module["could_not_be_compiled"] = True

                module["compile_error"] = extract_java_error_type(err)
                print(module["compile_error"], "\n\n")
                module["full_compile_error"] = err
            
            # delete the microbenchmark file
            try:
                os.remove(os.path.join(project["microbenchmarks_path"], class_name + ".java"))
            except Exception as e:
                print(f"Failed to delete {project['microbenchmarks_path']}: {e}")

    project["modules_with_no_generated_code"] = modules_with_no_generated_code
    project["modules_with_API_errors"] = modules_with_API_errors
    project["modules_with_unknown_errors"] = modules_with_unknown_errors
    project["modules_with_abstract_classes"] = abstract_classess
    project["modules_with_interfaces"] = interfeces
    project["modules_not_compiled"] = modules_not_compiled

    project["module_names_with_no_generated_code"] = module_names_with_no_generated_code
    project["module_names_with_API_errors"] = module_names_with_API_errors
    project["module_names_with_unknown_errors"] = module_names_with_unknown_errors
    project["module_names_with_abstract_classes"] = module_names_with_abstract_classes
    project["module_names_with_interfaces"] = module_names_with_interfaces
    project["module_names_that_did_not_compile"] = module_names_that_did_not_compile

    print(f"Finished compiling microbenchmarks for {project['name']}")
    print("----------------------------------------------------")
    print("total number of modules:", len(project["modules"]))
    print("modules with no generated code:", modules_with_no_generated_code)
    print("modules with API errors:", modules_with_API_errors)
    print("modules with unknown errors:", modules_with_unknown_errors)
    print("modules with abstract classes:", abstract_classess)
    print("modules with interfaces:", interfeces)
    print("modules not compiled:", modules_not_compiled)
    print("----------------------------------------------------")


def compile_microbenchmarks_for_all_projects(projects, generated_microbenchmarks_dir, abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str):
    for project in projects:
        compile_microbenchmarks_for_project(project, generated_microbenchmarks_dir, project["root_path"], project["has_maven"], abstract_class_found_str, interface_found_str, no_code_found_str, api_error_str, unknown_error_str)

def execute_compiled_microbenchmarks_for_project(project, generated_microbenchmarks_dir, root_path, has_maven):
    counter = 0

    modules_not_executed_successfully = 0
    module_names_that_did_not_execute_successfully = []
    modules_executed = 0

    # Activate the Java version for this project
    if "java_version" in project:
        try:
            if not is_java_version_installed(project["java_version"]):
                install_java_version(project["java_version"])
            activate_java_version(project["java_version"])
        except Exception as e:
            print(f"Failed to activate Java version for {project['name']} project: {e}")
            return
    
    # Install all project before moving on
    if has_maven:
        try: 
            subprocess.run(
                ["mvn", "spotless:apply"],
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            subprocess.run(
                ["mvn", "clean", "install", "-DskipTests"],
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except Exception as e:
            print(f"Failed to install {project['name']} project: {e}")
            return

    for module in project["modules"]:
        counter += 1
        class_name = module["name"]

        if not module["could_not_be_compiled"]:
            print(f"Executing microbenchmark number {counter} out of {len(project['modules'])}...")

            try:
                # Extract class name from test code
                match = re.search(r'\bpublic\s+class\s+([A-Za-z_]\w*)', module["test_code"])
                if match:
                    class_name = match.group(1)

                with open(os.path.join(project["microbenchmarks_path"], class_name + ".java"), "w") as f:
                    f.write(module["test_code"])
            except Exception as e:
                print(f"Failed to write to {project['microbenchmarks_path']}: {e}")
            
            try:
                if has_maven:
                    subprocess.run(
                        ["mvn", "clean", "verify"],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    subprocess.run(
                        ["java", "-jar", os.path.join("target", generated_microbenchmarks_dir + ".jar")],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                else:
                    subprocess.run(
                        ["./gradlew", f":{generated_microbenchmarks_dir}:clean", f":{generated_microbenchmarks_dir}:compileJmhJava", 
                         f":{generated_microbenchmarks_dir}:jmhJar", f":{generated_microbenchmarks_dir}:jmh", "--info", "--no-daemon", 
                         "--rerun-tasks"],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                modules_executed += 1
                module["executed_successfully"] = True
            except subprocess.CalledProcessError as e:
                error = ""

                if has_maven:
                    error = e.stdout
                else:
                    error = e.stderr

                module["execution_error"]= extract_java_error_type(error)
                module["full_execution_error"] = error
                module["executed_successfully"] = False
                modules_not_executed_successfully += 1
                module_names_that_did_not_execute_successfully.append(module["name"])

                print(f"Failed to execute {os.path.join(project['microbenchmarks_path'], class_name + '.java')}: {e}")
                print(module["execution_error"], "\n\n")
            except Exception as e:
                error = str(e)

                print(f"Failed to execute {os.path.join(project['microbenchmarks_path'], class_name + '.java')}: {e}")

                module["execution_error"]= extract_java_error_type(error)
                module["full_execution_error"] = error
                module["executed_successfully"] = False
                modules_not_executed_successfully += 1
                module_names_that_did_not_execute_successfully.append(module["name"])
    
    print("---------------------------------------------------------------")
    print(f"Executed {modules_executed} out of {len(project['modules'])} microbenchmarks successfully.")
    print(f"Failed to execute {modules_not_executed_successfully} out of {len(project['modules'])} microbenchmarks.")
    print("---------------------------------------------------------------")

def execute_compiled_microbenchmarks_for_all_projects(projects, generated_microbenchmarks_dir):
    for project in projects:
        execute_compiled_microbenchmarks_for_project(project, generated_microbenchmarks_dir, project["root_path"], project["has_maven"])

def extract_java_error_type(stderr_output: str):
    known_noise = [
        "COMPILATION ERROR",
        "COMPILATION FAILURE",
        "BUILD FAILURE",
        "Failed to execute goal",
    ]

    # 1. Catch classic Gradle/Maven [ERROR] lines
    for line in stderr_output.splitlines():
        if "[ERROR]" in line:
            msg = line.split("[ERROR]")[-1].strip()
            if not any(noise in msg for noise in known_noise):
                return msg

    # 2. Match javac-style error lines from Gradle (e.g., ';' expected, etc.)
    javac_error_pattern = re.compile(r".+\.java:\d+: error: .+")
    for line in stderr_output.splitlines():
        if javac_error_pattern.match(line.strip()):
            return line.strip()

    # 3. Fall back to generic "error:" keyword lines
    for line in stderr_output.splitlines():
        if "error:" in line.lower():
            return line.strip()

    # 4. Final fallback
    return stderr_output.strip().splitlines()[0] if stderr_output else "UnknownError"

def is_java_version_installed(java_version: str) -> bool:
    return os.path.exists(os.path.expanduser(f"~/.sdkman/candidates/java/{java_version}"))

def install_java_version(java_version: str):
    try:
        subprocess.run(
            f"bash -c 'source $HOME/.sdkman/bin/sdkman-init.sh && sdk install java {java_version} -y'",
            shell=True,
            executable="/bin/bash",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Java {java_version} using SDKMAN:\n{e.stderr}")
        raise e

def activate_java_version(java_version: str):
    try:
        subprocess.run(
            f"bash -c 'source $HOME/.sdkman/bin/sdkman-init.sh && sdk default java {java_version}'",
            shell=True,
            executable="/bin/bash",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to switch to Java {java_version} using SDKMAN:\n{e.stderr}")
        raise e