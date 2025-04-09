import configs
import clone
import static_analysis
import microbenchmarks_creation
import project_configuration
import data_collection
import utils

def main():
    projects = configs.PROJECTS_INFO
    clone.clone_projects(configs.PROJECTS_PATH, projects)
    project_configuration.configure_projects(projects, configs.JMH_POM_TEMPLATE)
    static_analysis.run_analysis_on_projects(projects)
    microbenchmarks_creation.create_microbenchmarks(projects, configs.PROMPT_ONE, configs.API_KEY, 
                configs.INTERFACE_FOUND, configs.ABSTRACT_CLASS_FOUND, configs.CODE_NOT_GENERATED, configs.API_ERROR, configs.UNKNOWN_ERROR, configs.MAX_RETRIES)
    data_collection.write_collected_data_in_json(projects, configs.DATA_COLLECTION_PATH)
    # projects = utils.read_projects(configs.DATA_COLLECTION_PATH, configs.PROJECT_NAMES)
    data_collection.compile_microbenchmarks_for_all_projects(projects, configs.GENERATED_MICROBENCHMARKS_DIR, 
                configs.ABSTRACT_CLASS_FOUND, configs.INTERFACE_FOUND, configs.CODE_NOT_GENERATED, configs.API_ERROR, configs.UNKNOWN_ERROR)
    data_collection.write_collected_data_in_json(projects, configs.DATA_COLLECTION_PATH)
    data_collection.execute_compiled_microbenchmarks_for_all_projects(projects, configs.GENERATED_MICROBENCHMARKS_DIR)
    data_collection.write_collected_data_in_json(projects, configs.DATA_COLLECTION_PATH)

    
    for project in projects:
        print(f"Finished compiling microbenchmarks for {project['name']}")
        print("----------------------------------------------------")
        print("total number of modules:", len(project["modules"]))
        print("modules with no generated code:", project["modules_with_no_generated_code"])
        print("modules with API errors:", project["modules_with_API_errors"])
        print("modules with unknown errors:", project["modules_with_unknown_errors"])
        print("modules with abstract classes:", project["modules_with_abstract_classes"])
        print("modules with interfaces:", project["modules_with_interfaces"])
        print("modules not compiled:", project["modules_not_compiled"])
        print("modules not executed successfully:", project["modules_not_executed_successfully"])
        print("modules executed successfully:", project["modules_executed"])
        print("----------------------------------------------------")

if __name__ == "__main__":
    main()