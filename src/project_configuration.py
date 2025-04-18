import os
import xml.etree.ElementTree as ET
import re

def configure_pom(parent_pom_path, child_pom_str, project_root_path, dependency_list, java_version):
    xmlns = "http://maven.apache.org/POM/4.0.0"
    namespace = f"{{{xmlns}}}"

    try:
        parent_tree = ET.parse(parent_pom_path)
    except Exception as e:
        print("Failed to parse parent POM:", e)
        exit(1)
    
    parent_root = parent_tree.getroot()

    child_root = ET.fromstring(child_pom_str)

    if child_root is None:
        raise Exception("Failed to parse POM")

    if parent_root is None:
        raise Exception("Failed to parse parent POM")

    # Add dependencies
    child_dependencies_el = child_root.find(namespace + "dependencies")
    if child_dependencies_el is None:
        child_dependencies_el = ET.SubElement(child_root, namespace + "dependencies")

    for dependency in dependency_list:
        child_dependency_el = ET.SubElement(child_dependencies_el, namespace + "dependency")
        child_dependency_groupId_el = ET.SubElement(child_dependency_el, namespace + "groupId")
        child_dependency_groupId_el.text = dependency["groupId"]
        child_dependency_artifactId_el = ET.SubElement(child_dependency_el, namespace + "artifactId")
        child_dependency_artifactId_el.text = dependency["artifactId"]
        child_dependency_version_el = ET.SubElement(child_dependency_el, namespace + "version")
        child_dependency_version_el.text = dependency["version"]
    
    # Add javac.target to properties tag
    child_properties_el = child_root.find(namespace + "properties")
    if child_properties_el is None:
        child_properties_el = ET.SubElement(child_root, namespace + "properties")

    child_javac_target_el = ET.SubElement(child_properties_el, namespace + "javac.target")
    child_javac_target_el.text = java_version.split(".")[0]

    ET.indent(parent_root, space="  ")
    ET.indent(child_root, space="  ")

    child_groupId_el = child_root.find(namespace + "groupId")
    child_artifactId_el = child_root.find(namespace + "artifactId")
    if child_groupId_el is None or child_artifactId_el is None:
        raise Exception("Failed to find groupId or artifactId in POM")

    # Make folders based on groupId and artifactId
    child_group_id = child_groupId_el.text
    child_artifact_id = child_artifactId_el.text
    
    package_path = os.path.join(*child_group_id.split("."))
    full_path = os.path.join(project_root_path, child_artifact_id, "src", "jmh", "java", package_path)

    try:
        os.makedirs(full_path, exist_ok=True)
    except Exception as e:
        print("Failed to create folders:", e)

    # Write parent changes back to file
    ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
    try:
        parent_tree.write(parent_pom_path, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        print("Failed to write parent POM:", e)

    # Write child pom to the given path
    try:
        with open(os.path.join(project_root_path, child_artifact_id, "pom.xml"), "w", encoding="utf-8") as f:
            f.write(ET.tostring(child_root, encoding='utf-8', method='xml').decode('utf-8'))
    except Exception as e:
        print("Failed to write child POM to file:", e)

    return full_path

def configure_gradle_project(project_root_path, jmh_module_name, java_version, dependency_list):
    settings_path = os.path.join(project_root_path, "settings.gradle")
    build_dir = os.path.join(project_root_path, jmh_module_name)
    build_gradle_path = os.path.join(build_dir, "build.gradle")

    # Ensure module folder exists
    destination_folder = os.path.join(build_dir, "src", "jmh", "java", "org", "ai", "bench", "jmh", "generated")
    os.makedirs(destination_folder, exist_ok=True)

    # Parse settings.gradle and extract module names (supports multiline includes) this big step is doen to see if :generated_jmh is included or not
    included_modules = []
    if os.path.exists(settings_path):
        include_block = []
        collecting = False

        try:
            with open(settings_path, "r") as f:
                for line in f:
                    stripped = line.strip().split("//")[0]  # Remove inline comments

                    if stripped.startswith("include"):
                        collecting = True
                        include_block.append(stripped)
                        if ")" in stripped or "," not in stripped:
                            collecting = False
                    elif collecting:
                        include_block.append(stripped)
                        if ")" in stripped:
                            collecting = False
        except Exception as e:
            print(f"Failed to read {settings_path}: {e}")
            exit(1)

        # Join all collected lines into one string and extract quoted module names
        include_text = " ".join(include_block)
        found = re.findall(r'["\']([^"\']+)["\']', include_text)

        included_modules = [f":{m}" if not m.startswith(":") else m for m in found]

    else:
        print(f"Failed to find settings.gradle in {project_root_path}")
        exit(1)

    # Add :generated_jmh to settings.gradle if it is not there already
    if f":{jmh_module_name}" not in included_modules:
        try:
            with open(settings_path, "a") as f:
                f.write(f'\ninclude(":{jmh_module_name}")\n')
            print(f"Added :{jmh_module_name} to settings.gradle")
        except Exception as e:
            print(f"Failed to append :{jmh_module_name} to settings.gradle: {e}")
            exit(1)

    # Add dependencies
    dep_lines = "\n".join(f'    implementation project("{m}")' for m in dependency_list)

    java_version_line = (
        f"JavaVersion.VERSION_1_8" if java_version.split(".")[0] == "8" else f"JavaVersion.toVersion({java_version.split('.')[0]})"
    )

    gradle_script = f"""
plugins {{
    id 'java'
    id 'me.champeau.jmh' version '0.7.2'
}}

repositories {{
    mavenCentral()
}}

dependencies {{
{dep_lines}
    jmh 'org.openjdk.jmh:jmh-core:1.37'
    jmh 'org.openjdk.jmh:jmh-generator-annprocess:1.37'
    jmh 'org.openjdk.jmh:jmh-generator-bytecode:1.37'
}}

sourceSets {{
    jmh {{
        java {{
            srcDirs = ['src/jmh/java']
        }}
    }}
}}

java {{
    sourceCompatibility = {java_version_line}
    targetCompatibility = {java_version_line}
}}

tasks.named("jmhJar") {{
    archiveFileName.set("{jmh_module_name}.jar")
}}
""".strip()

    try:
        with open(build_gradle_path, "w") as f:
            f.write(gradle_script)
    except Exception as e:
        print(f"Failed to write {build_gradle_path}: {e}")
        exit(1)

    print(f"Wrote {build_gradle_path} with dependencies from {len(dependency_list)} modules.")

    return destination_folder

def configure_projects(projects, pom_str, generated_jmh_dir):
    for project in projects:
        print(f"configuring {project['name']}")
        dependency_list = project.get("dependency_list", [])
        if project["has_maven"]:
            project["microbenchmarks_path"] = configure_pom(project["parent_pom_path"], pom_str, project["root_path"], dependency_list, project["java_version"])
        else:
            project["microbenchmarks_path"] = configure_gradle_project(project["root_path"], generated_jmh_dir, 
                                                                       project["java_version"], dependency_list)