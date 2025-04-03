import os
import xml.etree.ElementTree as ET
import re

def configure_pom(parent_pom_path, child_pom_str, project_root_path):
    xmlns = "http://maven.apache.org/POM/4.0.0"
    namespace = f"{{{xmlns}}}"

    try:
        parent_tree = ET.parse(parent_pom_path)
    except Exception as e:
        print("Failed to parse parent POM:", e)
        exit(1)
    
    parent_root = parent_tree.getroot()

    child_root = ET.fromstring(child_pom_str)

    if parent_root is None:
        raise Exception("Failed to parse parent POM")

    parent_group_id = parent_root.find(namespace + "groupId")
    parent_artifact_id = parent_root.find(namespace + "artifactId")
    parent_version = parent_root.find(namespace + "version")

    if parent_group_id is None or parent_artifact_id is None or parent_version is None:
        parent_parent_el = parent_root.find(namespace + "parent")
        if parent_parent_el is not None:
            parent_group_id = parent_parent_el.find(namespace + "groupId")
            parent_artifact_id = parent_parent_el.find(namespace + "artifactId")
            parent_version = parent_parent_el.find(namespace + "version")
            if parent_group_id is None or parent_artifact_id is None or parent_version is None:
                raise Exception("Failed to find parent groupId, artifactId or version")
        else:
            raise Exception("Failed to find parent groupId, artifactId or version")

    if child_root is None:
        raise Exception("Failed to parse child POM")

    # Add parent tag as child of child_root, i.e. project
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

    if child_root is None:
        raise Exception("Failed to parse POM")

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

def configure_gradle_project(project_root_path, jmh_module_name="generated_jmh"):
    settings_path = os.path.join(project_root_path, "settings.gradle")
    build_dir = os.path.join(project_root_path, jmh_module_name)
    build_gradle_path = os.path.join(build_dir, "build.gradle")

    # Ensure module folder exists
    destination_folder = os.path.join(build_dir, "src", "jmh", "java", "org", "ai", "bench", "jmh", "generated")
    os.makedirs(destination_folder, exist_ok=True)

    # Step 1: Parse settings.gradle and extract module names (supports multiline includes)
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

    # Fallback for single-module projects (no includes)
    if not included_modules or (len(included_modules) == 1 and included_modules[0] == f":{jmh_module_name}"):
        print("No includes found in settings.gradle, assuming single-module project.")
        included_modules = [":"]

    # Step 2: Append `include(":generated-jmh")` if not present
    if f":{jmh_module_name}" not in included_modules:
        try:
            with open(settings_path, "a") as f:
                f.write(f'\ninclude(":{jmh_module_name}")\n')
            print(f"Added :{jmh_module_name} to settings.gradle")
        except Exception as e:
            print(f"Failed to append :{jmh_module_name} to settings.gradle: {e}")
            exit(1)

    # Step 3: Filter out the generated module itself
    main_modules = [m for m in included_modules if m != f":{jmh_module_name}"]

    # Step 4: Write build.gradle for generated-jmh
    dep_lines = "\n".join(f'    implementation project("{m}")' for m in main_modules)

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
}}

java {{
    sourceCompatibility = JavaVersion.VERSION_1_8
    targetCompatibility = JavaVersion.VERSION_1_8
}}
""".strip()

    try:
        with open(build_gradle_path, "w") as f:
            f.write(gradle_script)
    except Exception as e:
        print(f"Failed to write {build_gradle_path}: {e}")
        exit(1)

    print(f"Wrote {build_gradle_path} with dependencies from {len(main_modules)} modules.")

    return destination_folder

def configure_projects(projects, pom_str):
    for project in projects:
        print(f"configuring {project['name']}")
        if project["has_maven"]:
            project["microbenchmarks_path"] = configure_pom(project["parent_pom_path"], pom_str, project["root_path"])
        else:
            project["microbenchmarks_path"] = configure_gradle_project(project["root_path"])