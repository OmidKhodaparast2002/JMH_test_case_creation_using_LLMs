"""
analysis pipeline takes the microbenchmarks created by the generate pipeline and placed in 
relative folders of each project to compile and run them and create a report that showcases 
the result of benchmark executions such as compilation rate, successful run rate, and code coverage.

"""
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

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
        if project['has_jmh'] == "True":
            continue

        if project['has_maven'] == "True":
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

    return

def compile_benchmarks(project_data:dict):
    """
    This function compiles the llm generated benchmarks and store the results into the report file.

    Args:
        project_data (dict): projects configuration
    """
    return

def run_benchmarks(project_data:dict):
    """
    This function runs the successfully compiled benchmakrks and runs them and store the results into
    the report file.

    Args:
        project_data (dict): projects configuration
    """
    return

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