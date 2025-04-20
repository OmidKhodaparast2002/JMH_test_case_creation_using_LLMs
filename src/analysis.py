"""
analysis pipeline takes the microbenchmarks created by the generate pipeline and placed in 
relative folders of each project to compile and run them and create a report that showcases 
the result of benchmark executions such as compilation rate, successful run rate, and code coverage.

"""
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import subprocess

JMH_VERSION = "1.37"

def prettify(elem):
    """Return pretty printed XML string."""
    return minidom.parseString(ET.tostring(elem)).toprettyxml(indent="  ")

def find_or_create(parent, tag):
    found = parent.find(tag)
    if found is None:
        found = ET.SubElement(parent, tag)
    return found

def dependency_exists(dependencies, groupId, artifactId):
    for dep in dependencies.findall("dependency"):
        g = dep.find("groupId")
        a = dep.find("artifactId")
        if g is not None and a is not None and g.text == groupId and a.text == artifactId:
            return True
    return False

def plugin_exists(plugins, groupId, artifactId):
    for plugin in plugins.findall("plugin"):
        g = plugin.find("groupId")
        a = plugin.find("artifactId")
        if g is not None and a is not None and g.text == groupId and a.text == artifactId:
            return True
    return False

def setup_configs(project_data: dict):
    """
    This function sets up every step needed such as configuring Maven/Gradle files in order to 
    compile and run designated benchmarks and also cleans up after previous runs for a fresh start.

    Args:
        project_data (dict): projects configuration 
    """
    for project in project_data["projects"]:

        project_root = Path(project["root_path"])

        

        if project['has_maven'] == "True":
            project["project_classpath"] = get_maven_classpath(project_root)
            pom_path = project['parent_pom_path']
            tree = ET.parse(pom_path)
            root = tree.getroot()

            ns = {'mvn': root.tag.split('}')[0].strip('{')}
            ET.register_namespace('', ns['mvn'])

            # Add dependencies
            dependencies = root.find("mvn:dependencies", ns)
            if dependencies is None:
                dependencies = ET.SubElement(root, "dependencies")

            # JMH core
            if not dependency_exists(dependencies, "org.openjdk.jmh", "jmh-core"):
                dep = ET.SubElement(dependencies, "dependency")
                ET.SubElement(dep, "groupId").text = "org.openjdk.jmh"
                ET.SubElement(dep, "artifactId").text = "jmh-core"
                ET.SubElement(dep, "version").text = JMH_VERSION

            # JMH annotation processor
            if not dependency_exists(dependencies, "org.openjdk.jmh", "jmh-generator-annprocess"):
                dep = ET.SubElement(dependencies, "dependency")
                ET.SubElement(dep, "groupId").text = "org.openjdk.jmh"
                ET.SubElement(dep, "artifactId").text = "jmh-generator-annprocess"
                ET.SubElement(dep, "version").text = JMH_VERSION
                ET.SubElement(dep, "scope").text = "provided"

            # Add plugin
            build = root.find("mvn:build", ns)
            if build is None:
                build = ET.SubElement(root, "build")

            plugins = build.find("mvn:plugins", ns)
            if plugins is None:
                plugins = ET.SubElement(build, "plugins")

            if not plugin_exists(plugins, "org.apache.maven.plugins", "maven-compiler-plugin"):
                plugin = ET.SubElement(plugins, "plugin")
                ET.SubElement(plugin, "groupId").text = "org.apache.maven.plugins"
                ET.SubElement(plugin, "artifactId").text = "maven-compiler-plugin"
                ET.SubElement(plugin, "version").text = "3.8.1"

                config = ET.SubElement(plugin, "configuration")
                annotationPaths = ET.SubElement(config, "annotationProcessorPaths")
                path = ET.SubElement(annotationPaths, "path")
                ET.SubElement(path, "groupId").text = "org.openjdk.jmh"
                ET.SubElement(path, "artifactId").text = "jmh-generator-annprocess"
                ET.SubElement(path, "version").text = JMH_VERSION

            # Save file
            with open(pom_path, "w", encoding="utf-8") as f:
                f.write(prettify(root))

            print(f"✅ Injected JMH into: {pom_path}")

        elif project["has_maven"] == "False":
            project["project_classpath"] = get_gradle_classpath(project_root)


    return

def compile_and_run_benchmarks(project_data: dict):
    """
    This function compiles the LLM-generated benchmarks and stores the success/failure results.

    Args:
        project_data (dict): projects configuration
    """
    for project in project_data['projects']:
        path_to_benchmarks = Path(project['llm_benchmarks_path'])
        project_classpath = project['project_classpath']  # Should include project dependencies

        if path_to_benchmarks.is_dir():
            benchmarks = list(path_to_benchmarks.rglob("*.java"))

            total = 0
            successful_compile = 0
            successful_run = 0

            for benchmark_file in benchmarks:
                total += 1
                benchmark_path = str(benchmark_file)
                output_dir = path_to_benchmarks / "compiled"
                output_dir.mkdir(exist_ok=True)

                try:
                    # Compile the benchmark
                    subprocess.run(
                        [
                            "javac",
                            "-cp",
                            project_classpath,
                            "-d",
                            str(output_dir),
                            benchmark_path,
                        ],
                        check=True,
                        capture_output=True
                    )
                    successful_compile += 1

                    # Extract the class name from the file (e.g. BenchmarkFoo.java -> BenchmarkFoo)
                    class_name = benchmark_file.stem
                    package = extract_package(benchmark_file)  # helper (see below)
                    full_class_name = f"{package}.{class_name}" if package else class_name

                    # Run the compiled benchmark
                    subprocess.run(
                        [
                            "java",
                            "-cp",
                            f"{output_dir}:{project_classpath}",
                            "org.openjdk.jmh.Main",
                            full_class_name
                        ],
                        check=True,
                        capture_output=True
                    )
                    successful_run += 1

                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Benchmark {benchmark_file.name} failed:\n{e.stderr.decode()}")

            print(
                f"Project {project['name']}: Total={total}, "
                f"Compiled={successful_compile}, Ran={successful_run}"
            )


    return

def get_gradle_classpath(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["./gradlew", "dependencies", "--configuration", "runtimeClasspath"],
            cwd=project_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Optional: If you want a machine-usable classpath, create a custom Gradle task
        # For now, just return compiled classes directory
        return f"{project_root / 'build/classes/java/main'}"
    except subprocess.CalledProcessError as e:
        print(f"Error while generating Gradle classpath: {e.stderr.decode()}")
        return ""

import subprocess

def get_maven_classpath(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["mvn", "dependency:build-classpath", "-Dmdep.outputFile=cp.txt"],
            cwd=project_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        classpath_file = project_root / "cp.txt"
        with open(classpath_file, "r") as f:
            deps_cp = f.read().strip()

        # Add target/classes to include compiled project classes
        return f"{deps_cp}:{project_root / 'target/classes'}"
    except subprocess.CalledProcessError as e:
        print(f"Error while generating Maven classpath: {e.stderr.decode()}")
        return ""


def extract_package(java_file_path: Path) -> str:
    """
    Extracts the package declaration from a .java file.
    """
    with java_file_path.open('r') as f:
        for line in f:
            if line.strip().startswith("package"):
                return line.strip().split()[1].rstrip(";")
    return ""

def compare_code_coverage(project_data:dict):
    """
    This function compares the code coverage between original benchamarks and llm generated benchmarks
    for the projects that come with microbenchmarking and stores the result into the report file.
    
    Args:
        proeject_data (dict): projects configuration
    """
    return

def add_report(report_file: Path, report: str):
    """
    This function takes a file path and a string to add the given report to the bottom of the existing
    report.

    Args:
        report_file (Path): Path to the report file
        report (str): Report content that will be added to the existing report content
    """

    with open(report_file, 'a') as file:
        file.write(report)

    return


def analyze(project_data:dict, report_file: Path):
    """
    This is the full pipeline that sets up, compiles, runs, and makes the final report of the given
    projects 

    Args:
        project_data (dict): projects configuration
        report_file (Path): Path to the final report
    """
    return