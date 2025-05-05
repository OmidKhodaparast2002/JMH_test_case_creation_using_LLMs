import utils
import os
import subprocess
import re
from typing import Dict, List
import shlex
import time

# We use this when subprocess.run() throws an exception other than CalledProcessError
NOT_RUN_EXCEPTION_ERR_STR = "SOMETHING WENT WRONG"

def write_collected_data_in_json(projects, path):
    if not utils.folder_exists(path):
        utils.create_folder(path)
        
    for project in projects:
        utils.write_json(project, os.path.join(path, project["name"] + ".json"))

def compile_and_execute_microbenchmarks_for_project(project, generated_microbenchmarks_dir, no_code_found_str, 
                                                    api_error_str, unknown_error_str, package_path, compile_erros_list):
    counter = 0
    
    modules_with_no_generated_code = 0
    modules_compiled = 0
    modules_with_API_error = 0
    modules_with_unknown_error = 0

    module_names_with_no_generated_code = []
    module_names_that_did_not_compile = []
    module_names_with_API_error = []
    module_names_with_unknown_error = []

    err = None

    modules_not_executed_successfully = 0
    module_names_that_did_not_execute_successfully = []
    modules_executed_sucessfully = 0

    total_num_of_benchmarks = 0
    num_of_benchmarks_compiled = 0
    num_of_benchmarks_executed = 0

    benchamrks = None
    benchmark_results = None

    execution_return_code = None
    cwd = None
    jar_dir = None

    root_path = project["root_path"]
    has_maven = project["has_maven"]

    # Activate the Java version for this project
    if "java_version" in project:
        try:
            if not utils.is_java_version_installed(project["java_version"]):
                utils.install_java_version(project["java_version"])
            utils.activate_java_version(project["java_version"])
        except Exception as e:
            print(f"Failed to activate Java version for {project['name']} project: {e}")
            return

        if "JAVA_HOME" not in os.environ:
            os.environ["JAVA_HOME"] = os.path.expanduser("~/.sdkman/candidates/java/current")
            os.environ["PATH"] = os.path.join(os.environ["JAVA_HOME"], "bin") + ":" + os.environ["PATH"]

    # Install all project before moving on
    if has_maven:
        try: 
            subprocess.run(
                ["mvn", "clean", "install", "-DskipTests", "-Drat.skip=true", "-Dbnd.baseline.skip=true", "-Dspotless.check.skip=true"],
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except Exception as e:
            print(f"Failed to install {project['name']} project: {str(e)}")
            return

    for module in project["modules"]:
        counter += 1
        print(f"compiling module number {counter} out of {len(project['modules'])}...")

        class_name = module["name"][0:len(module["name"]) - 5]

        if module["test_code"] == no_code_found_str:
            modules_with_no_generated_code += 1
            module_names_with_no_generated_code.append(module["name"])
        elif module["test_code"] == api_error_str:
            modules_with_API_error += 1
            module["could_not_be_compiled"] = True
            module_names_with_API_error.append(module["name"])
        elif module["test_code"] == unknown_error_str:
            modules_with_unknown_error += 1
            module_names_with_unknown_error.append(module["name"])
        else:
            try:
                # Extract class name from test code
                match = re.search(r'\bpublic\s+class\s+([A-Za-z_]\w*)', module["test_code"])
                if match:
                    class_name = match.group(1)

                with open(os.path.join(project["microbenchmarks_path"], class_name + ".java"), "w") as f:
                    code = module["test_code"]
                    # Remove any existing package statement
                    code = utils.remove_existing_package_statement(code)
                    # add package statement
                    code = f"package {package_path};\n" + code
                    f.write(code)
            except Exception as e:
                print(f"Failed to write to {module['name']} {project['microbenchmarks_path']}: {e}")
                continue

            benchamrks = utils.extract_benchmark_names(module["test_code"])
            module["benchmarks"] = benchamrks

            try:
                if has_maven:
                    subprocess.run(
                        ["mvn", "clean", "verify", "-Drat.skip=true", "-Dbnd.baseline.skip=true", "-Dspotless.check.skip=true"],
                        cwd=os.path.join(root_path, generated_microbenchmarks_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=os.environ,
                        text=True,
                        check=True
                    )
                else:
                    subprocess.run(
                        ["./gradlew", f":{generated_microbenchmarks_dir}:clean", 
                         f":{generated_microbenchmarks_dir}:jmhJar", "--info", "--no-daemon"],
                        cwd=root_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=os.environ,
                        text=True,
                        check=True
                    )
                module["could_not_be_compiled"] = False
                modules_compiled += 1
            except subprocess.CalledProcessError as e:
                err = ''

                if project["has_maven"]:
                    err = e.stdout
                else:
                    err = e.stderr

                print(f"Failed to compile {class_name}.java.")

                module_names_that_did_not_compile.append(module["name"])
                module["could_not_be_compiled"] = True

                module["compile_errors"] = extract_compile_error_types(err, compile_erros_list)
                print(module["compile_errors"])
                # print("full_error:", err)
                module["full_compile_error"] = err
            except Exception as e:
                err = str(e)

                print(f"Failed to compile {class_name}'.java'). SOMETHING WENT WRONG. THE ERROR WAS: {err}.")

                module_names_that_did_not_compile.append(module["name"])
                module["could_not_be_compiled"] = True

                module["compile_errors"] = [NOT_RUN_EXCEPTION_ERR_STR]
                module["full_compile_error"] = NOT_RUN_EXCEPTION_ERR_STR
            
            # Compilation, succeded. Now we execute
            if not module["could_not_be_compiled"]:
                print(f"Executing module number {counter} out of {len(project['modules'])}...")
                # JMH does not return non-zero return code, even if benchmark thorws runtime exceptions
                if has_maven:
                    cwd = os.path.join(root_path, generated_microbenchmarks_dir)
                    jar_dir = "target"
                else:
                    cwd = root_path
                    jar_dir = os.path.join(generated_microbenchmarks_dir, "build", "libs")
                
                command = f"java -jar {jar_dir}/{generated_microbenchmarks_dir}.jar -wi 0 -i 1 -f1 -to 180"
                
                execution_return_code, benchmark_results, execution_error = stream_and_analyze_jmh_output(command, cwd, class_name, package_path)

                if execution_return_code == 0:
                    module["benchmark_results"] = benchmark_results
                    module["could_not_be_executed"] = False
                    modules_executed_sucessfully += 1
                else:
                    module["benchmark_results"] = benchmark_results
                    module["could_not_be_executed"] = True
                    module["execution_error"] = execution_error
                    modules_not_executed_successfully += 1
                    module_names_that_did_not_execute_successfully.append(module["name"])

            # delete the microbenchmark file
            try:
                os.remove(os.path.join(project["microbenchmarks_path"], class_name + ".java"))
            except Exception as e:
                err = str(e)
                print(f"Failed to delete {class_name}.java. {err}")
            
            total_num_of_benchmarks += len(module["benchmarks"])

            if not module["could_not_be_compiled"]:
                num_of_benchmarks_compiled += len(module["benchmarks"])
                if not module["could_not_be_executed"]:
                    for bench_res in module["benchmark_results"]:
                        if bench_res["is_executed_successfully"]:
                            num_of_benchmarks_executed += 1
                else:
                    num_of_benchmarks_executed += len(module["benchmarks"])
        
        print("\n\n")
        benchamrks = None
        execution_return_code = None
        cwd = None
        jar_dir = None
        benchmark_results = None

    project["modules_with_no_generated_code"] = modules_with_no_generated_code
    project["modules_compiled"] = modules_compiled

    project["module_names_with_no_generated_code"] = module_names_with_no_generated_code
    project["module_names_that_did_not_compile"] = module_names_that_did_not_compile

    project["total_num_of_benchmarks"] = total_num_of_benchmarks
    project["num_of_benchmarks_compiled"] = num_of_benchmarks_compiled
    project["num_of_benchmarks_executed"] = num_of_benchmarks_executed
    project["modules_with_API_error"] = modules_with_API_error
    project["modules_with_unknown_error"] = modules_with_unknown_error

    project["modules_not_executed_successfully"] = modules_not_executed_successfully
    project["modules_executed_sucessfully"] = modules_executed_sucessfully
    project["module_names_that_did_not_execute_successfully"] = module_names_that_did_not_execute_successfully

    print(f"Finished compiling and executing microbenchmarks for {project['name']}")
    print("----------------------------------------------------")
    print("total number of modules:", len(project["modules"]))
    print("modules with no generated code:", modules_with_no_generated_code)
    print("modules with api errors:", modules_with_API_error)
    print("modules with unknown errors:", modules_with_unknown_error)
    print("modules compiled:", modules_compiled)
    print("total number of benchmarks:", total_num_of_benchmarks)
    print("number of benchmarks tha compiled:", num_of_benchmarks_compiled)
    print("number of benchmarks that executed:", num_of_benchmarks_executed)
    print("----------------------------------------------------")

def compile_and_execute_microbenchmarks_for_all_projects(projects, generated_microbenchmarks_dir, no_code_found_str, api_error_str, 
                                                         unknown_error_str, packahe_path, data_collection_path, compile_erros_list, projects_to_ignore):
    for project in projects:
        if project["name"] in projects_to_ignore:
            continue
        compile_and_execute_microbenchmarks_for_project(project, generated_microbenchmarks_dir,
                                no_code_found_str, api_error_str, unknown_error_str, packahe_path, compile_erros_list)
        write_collected_data_in_json(projects, data_collection_path)

def extract_compile_error_types(stderr_output: str, compile_errors_list: list[str]) -> list[str]:
    matched_errors = []
    for pattern in compile_errors_list:
        if re.search(pattern, stderr_output, flags=re.IGNORECASE):
            matched_errors.append(pattern)
    return matched_errors if matched_errors else ["Other Category"]

def stream_and_analyze_jmh_output(command, cwd, class_name, package_path, timeout_minutes=20):
    benchmark_results = []
    current_benchmark = None
    collected_lines = []
    timeout_seconds = timeout_minutes * 60
    time_out_reached = False
    stderr_output = ""

    pattern = re.compile(rf"# Benchmark:\s+{re.escape(package_path)}\.{re.escape(class_name)}\.(\w+)")

    start_time = time.time()

    try:
        with subprocess.Popen(shlex.split(command), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=os.environ) as proc:

            for line in proc.stdout:
                elasped_time = time.time() - start_time
                if elasped_time > timeout_seconds:
                    time_out_reached = True
                    proc.kill()
                    break


                print(line.strip())  # Optional: for real-time logging
                match = pattern.match(line)
                if match:
                    # Flush previous benchmark result
                    if current_benchmark and collected_lines:
                        res = flush(current_benchmark, collected_lines)
                        if res:
                            benchmark_results.append(res)
                    current_benchmark = match.group(1)
                    collected_lines = []
                elif current_benchmark:
                    collected_lines.append(line)

            # Final flush
            if current_benchmark and collected_lines:
                res = flush(current_benchmark, collected_lines)
                if res:
                    benchmark_results.append(res)
            
            stderr_output = proc.stderr.read()

        proc.wait()

        if time_out_reached:
            return -1, benchmark_results, "Timeout reached"

        # Deduplicate by benchmark name
        deduped = {}
        for result in benchmark_results:
            name = result["name"]
            if name not in deduped:
                deduped[name] = result

        print(f"Execution return code: {proc.returncode}")
        if proc.returncode != 0:
            print("error in jmh jar execution:", stderr_output)
            return proc.returncode, [], stderr_output
        return proc.returncode, list(deduped.values()), None

    except KeyboardInterrupt:
        proc.kill()
        return -1, benchmark_results, "JMH blcoked"
    except Exception as e:
        print(f"Failed to stream benchmark output: {str(e)}")
        return -1, [], "Popen failed"

def flush(current_benchmark, collected_lines):
    if current_benchmark:
        success, error = parse_benchmark_result(collected_lines)
        bench_info = {
            "name": current_benchmark,
            "is_executed_successfully": success
        }

        if not success:
            bench_info["error"] = error
        
        return bench_info
    return None

def parse_benchmark_result(lines):
    for i, line in enumerate(lines):
        if "<failure>" in line:
            # Look ahead for the actual error
            for j in range(i+1, len(lines)):
                l = lines[j].strip()
                if l.startswith("java.") or l.startswith("org."):
                    return False, l.split(":")[0]
            return False, "UnknownError"
        elif line.strip().startswith("Iteration"):
            return True, ""
    return False, "NoIterationDetected"


