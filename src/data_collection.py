import utils
import os
import subprocess
import re
from typing import Dict, List
import shlex
import time
import threading
import random
import shutil

# We use this when subprocess.run() throws an exception other than CalledProcessError
NOT_RUN_EXCEPTION_ERR_STR = "SOMETHING WENT WRONG"
# This timeout is used to kill JMH process if no output is received
JMH_TIMEOUT_SECONDS = 120
# This time is used as the thread check interval
CHECK_INTERVAL = 10

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
                
                command = f"java -Xms2g -Xmx4g -jar {jar_dir}/{generated_microbenchmarks_dir}.jar -wi 0 -i 1 -f1 -to 60"
                
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
    last_output_time = time.time()
    watchdog_triggered = threading.Event()

    pattern = re.compile(rf"# Benchmark:\s+{re.escape(package_path)}\.{re.escape(class_name)}\.(\w+)")

    def watchdog(proc, check_interval=CHECK_INTERVAL, timeout_without_output=JMH_TIMEOUT_SECONDS):
        nonlocal last_output_time
        while proc.poll() is None:
            time.sleep(check_interval)
            if time.time() - last_output_time > timeout_without_output:
                print(f"[Watchdog] No output for {timeout_without_output} seconds. Killing JMH process...")
                proc.kill()
                watchdog_triggered.set()
                break

    start_time = time.time()

    try:
        with subprocess.Popen(shlex.split(command), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=os.environ) as proc:

            # Start watchdog thread
            monitor = threading.Thread(target=watchdog, args=(proc,))
            monitor.daemon = True
            monitor.start()

            for line in proc.stdout:
                elasped_time = time.time() - start_time
                if elasped_time > timeout_seconds:
                    time_out_reached = True
                    proc.kill()
                    break
                
                last_output_time = time.time()

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

        if watchdog_triggered.is_set():
            return -1, benchmark_results, "JMH blocked"

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

def collect_coverage_on_projects_with_jmh(projects, generated_microbenchmarks_dir, projects_to_ignore, package_path):
    for project in projects:
        if project["name"] in projects_to_ignore:
            continue
        if project["has_jmh"]:
            collect_coverage_on_one_project(project, generated_microbenchmarks_dir, package_path)

def collect_coverage_on_one_project(project, generated_microbenchmarks_dir, package_path):
    has_maven = project["has_maven"]
    root_path = project["root_path"]
    jacoco_exec_save_path_human = os.path.join("exec", "human_written", "jacoco-jmh.exec")
    jacoco_exec_save_path_llm = os.path.join("exec", "llm_written", "jacoco-jmh.exec")
    report_os_save_path_llm = os.path.join("..", "data", "coverage", project["name"], "llm")
    report_os_save_path_human = os.path.join("..", "data", "coverage", project["name"], "human")
    jacoco_report_save_path_llm = os.path.join("..", "..", "data", "collected", "coverage", project["name"], "llm")
    jacoco_report_save_path_human = os.path.join("..", "..", "data", "collected", "coverage", project["name"], "human")

    project_class_path = project["class_path"]
    project_source_path = project["source_path"]

    cwd = root_path
    jar_dir = None

    jmh_root_dir_name = project["jmh_root_dir_name"]
    jmh_root_dir_name_copy = jmh_root_dir_name + "-copy"

    # Create folders where the html report will be saved
    os.makedirs(report_os_save_path_llm, exist_ok=True)
    os.makedirs(report_os_save_path_human, exist_ok=True)

    # Create folders for saving jacoco exec
    os.makedirs(os.path.join(root_path, "exec", "human_written"), exist_ok=True)
    os.makedirs(os.path.join(root_path, "exec", "llm_written"), exist_ok=True)

    # Get java agent
    java_agent_human = f"-javaagent:{os.path.expanduser(os.path.join("~", "jacoco", "lib", "jacocoagent.jar"))}=destfile={jacoco_exec_save_path_human}"
    java_agent_llm = f"-javaagent:{os.path.expanduser(os.path.join("~", "jacoco", "lib", "jacocoagent.jar"))}=destfile={jacoco_exec_save_path_llm}"
    # get Jacoco cli
    jacoco_cli_path = f"{os.path.expanduser(os.path.join("~", "jacoco", "lib", "jacococli.jar"))}"

    print(f"Collecting coverage for {project['name']} project")
    
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
    else:
        try:
            subprocess.run(["./gradlew", "clean", "classes"], 
                cwd=root_path, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True)
        except Exception as e:
            print(f"Failed to install {project['name']} project: {str(e)}")
            return
        
    # create a jar file containing the class path of the directory we want coverage on
    try:
        subprocess.run(["bash", "-c", f"jar -cf {project['name']}.jar -C {project_class_path} ."], 
            cwd=root_path, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True)
        
        print(f"Created jar file for {project['name']} project")
    except Exception as e:
        print(f"Failed to create jar file for {project['name']} project: {str(e)}")
        return
    
    # create a copy of project's jmh directory
    try:
        shutil.copytree(os.path.join(root_path, jmh_root_dir_name), os.path.join(root_path, jmh_root_dir_name_copy))
    except Exception as e:
        print(f"Failed to copy jmh directory for {project['name']} project: {str(e)}")
    
    pick_microbenhmark_suits_for_coverage(project, package_path)

    # Compile generated micorbenchmarks
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
    except Exception as e:
        print(f"Failed to compile generated microbenchmarks for {project['name']} project: {str(e)}")
        return
    
    # Compile project's own jmh
    try:
        if has_maven:
            subprocess.run(
                ["mvn", "clean", "verify", "-Drat.skip=true", "-Dbnd.baseline.skip=true", "-Dspotless.check.skip=true"],
                cwd=os.path.join(root_path, project["jmh_sub_module"]),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ,
                text=True,
                check=True
            )
        else:
            subprocess.run(
                shlex.split(project["compile_command"]),
                cwd=root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ,
                text=True,
                check=True
            )
    except Exception as e:
        print(f"Failed to compile project's own jmh for {project['name']} project: {str(e)}")
        return
    
    # execute llm generated microbenchmarks
    if has_maven:
        jar_dir = os.path.join(generated_microbenchmarks_dir, "target")
    else:
        jar_dir = os.path.join(generated_microbenchmarks_dir, "build", "libs")
    
    execution_command = f"java -Djacoco.debug=true -Xms2g -Xmx4g {java_agent_llm} -cp {project["name"]}.jar:{os.path.join(jar_dir, generated_microbenchmarks_dir + ".jar")} org.openjdk.jmh.Main -wi 0 -i 1 -f0 -to 60"
    try:
        with subprocess.Popen(shlex.split(execution_command), cwd=cwd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=os.environ) as process:
            
            for line in process.stdout:
                print(line.strip())
            
            process.wait()
    except Exception as e:
        print(f"Failed to execute generated microbenchmarks for {project['name']} project: {str(e)}")
        return
    
    # check the exec file
    try:
        print("checking exec file for llm generated microbenchmarks")
        subprocess.run(["java", "-jar", jacoco_cli_path, "execinfo", jacoco_exec_save_path_llm],
            cwd=root_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True)
    except Exception as e:
        print(f"Failed to check generated microbenchmarks for {project['name']} project: {str(e)}")
        return

    # execute project's own jmh
    jar_dir = project["project_jmh_jar_path"]

    execution_command = f"java -Djacoco.debug=true -Xms2g -Xmx4g {java_agent_human} -cp {project["name"]}.jar:{os.path.join(jar_dir, project["produced_jmh_jar_name"])} org.openjdk.jmh.Main -wi 0 -i 1 -f0 -to 60"
    try:
        with subprocess.Popen(shlex.split(execution_command), cwd=cwd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=os.environ) as process:
            
            for line in process.stdout:
                print(line.strip())

            process.wait()
    except Exception as e:
        print(f"Failed to execute project's own jmh for {project['name']} project: {str(e)}")
        return
    
    # check the exec file
    try:
        print("checking exec file for project's own jmh")
        subprocess.run(["java", "-jar", jacoco_cli_path, "execinfo", jacoco_exec_save_path_human],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True)
    except Exception as e:
        print(f"Failed to check generated microbenchmarks for {project['name']} project: {str(e)}")
        return
    
    # generate jacoco report for llm generated microbenchmarks
    execution_command = f"java -Xms2g -Xmx4g -jar {jacoco_cli_path} report {jacoco_exec_save_path_llm} --classfiles {project_class_path} --sourcefiles {project_source_path} --html {jacoco_report_save_path_llm}"
    try:
        with subprocess.Popen(shlex.split(execution_command), cwd=cwd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=os.environ) as process:
            
            for line in process.stdout:
                print(line.strip())
            
            process.wait()
    except Exception as e:
        print(f"Failed to generate jacoco report for llm generated microbenchmarks for {project['name']} project: {str(e)}")
        return
    
    # generate jacoco report for project's own jmh
    execution_command = f"java -Xms2g -Xmx4g -jar {jacoco_cli_path} report {jacoco_exec_save_path_human} --classfiles {project["class_path"]} --sourcefiles {project["source_path"]} --html {jacoco_report_save_path_human}"
    try:
        with subprocess.Popen(shlex.split(execution_command), cwd=cwd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=os.environ) as process:
            
            for line in process.stdout:
                print(line.strip())
            
            process.wait()
    except Exception as e:
        print(f"Failed to generate jacoco report for project's own jmh for {project['name']} project: {str(e)}")
        return
    
    # The project jmh root copy becomes the actual one and we delete the one we used for execution
    try:
        shutil.rmtree(os.path.join(root_path, jmh_root_dir_name))
        os.rename(os.path.join(root_path, jmh_root_dir_name_copy), os.path.join(root_path, jmh_root_dir_name))
    except Exception as e:
        print(f"Failed to delete {jmh_root_dir_name} for {project['name']} project: {str(e)}")
        return

    print(f"Successfully gathered coverage data for {project['name']} project\n\n")

def pick_microbenhmark_suits_for_coverage(project: dict, package_path):
    human_written_micorbenchmark_suits_num = project.get("number_of_benchmarks_suits", None)
    generated_benchmarks_suits_num = project.get("modules_compiled", None)
    human_written_benchmark_suits_path = project.get("jmh_path", None)


    if human_written_micorbenchmark_suits_num is None or generated_benchmarks_suits_num is None or human_written_benchmark_suits_path is None:
        print("Not enough information to write microbenchmark suits")
        raise DicAttDoesNotExist("Not enough information to write microbenchmark suits")
    
    if human_written_micorbenchmark_suits_num > generated_benchmarks_suits_num:
        print("more human written microbenchmarks than generated ones")
        pick_random_human_written_microbenchmark_suits(human_written_benchmark_suits_path, generated_benchmarks_suits_num)
    else:
        print("more generated microbenchmarks than human written ones")
        pick_random_generated_microbenchmark_suits(project, human_written_micorbenchmark_suits_num, package_path)


def pick_random_generated_microbenchmark_suits(project, number_suits_needed, package_path):
    modules_compiled = [module for module in project["modules"] if not module["could_not_be_compiled"]]
    modules_successfully_executed = [module for module in modules_compiled if not module["could_not_be_executed"]]
    random.shuffle(modules_successfully_executed)
    for i in range(number_suits_needed):
        try:
            # Extract class name from test code
            match = re.search(r'\bpublic\s+class\s+([A-Za-z_]\w*)', modules_successfully_executed[i]["test_code"])
            if match:
                class_name = match.group(1)

            with open(os.path.join(project["microbenchmarks_path"], class_name + ".java"), "w") as f:
                code = modules_successfully_executed[i]["test_code"]
                # Remove any existing package statement
                code = utils.remove_existing_package_statement(code)
                # add package statement
                code = f"package {package_path};\n" + code
                f.write(code)
        except Exception as e:
            print(f"Failed to write to {modules_successfully_executed[i]['name']} {project['microbenchmarks_path']}: {e}")
            continue
        

def pick_random_human_written_microbenchmark_suits(jmh_benchmarks_path, number_suits_needed):
    # Gather all .java files
    all_files = []
    for root, dirs, files in os.walk(jmh_benchmarks_path):
        for file in files:
            if file.endswith(".java"):
                all_files.append(os.path.join(root, file))

    # This if statement should never be triggered
    if number_suits_needed >= len(all_files):
        print("No files need to be removed — human-written benchmarks are already fewer or equal.")
        return

    # Shuffle and pick files to keep
    random.shuffle(all_files)
    files_to_keep = set(all_files[:number_suits_needed])
    files_to_remove = [f for f in all_files if f not in files_to_keep]

    # Remove unneeded files
    for path in files_to_remove:
        try:
            os.remove(path)
        except Exception as e:
            print(f"Failed to remove {path}: {e}")

class DicAttDoesNotExist(Exception):
    pass