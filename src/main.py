import configs
import clone
import static_analysis
import microbenchmarks_creation
import project_configuration
import data_collection
import utils

def main():
    projects = configs.PROJECTS_INFO
    collection_path = configs.DATA_COLLECTION_PATH
    clone.clone_projects(configs.PROJECTS_PATH, projects, configs.GENERATED_MICROBENCHMARKS_DIR)
    project_configuration.configure_projects(projects, configs.JMH_POM_TEMPLATE, configs.GENERATED_MICROBENCHMARKS_DIR)
    static_analysis.run_analysis_on_projects(projects)
    data_collection.write_collected_data_in_json(projects, collection_path)
    microbenchmarks_creation.create_microbenchmarks(projects, configs.PROMPT_ONE, configs.API_KEY, 
                configs.INTERFACE_FOUND, configs.ABSTRACT_CLASS_FOUND, configs.CODE_NOT_GENERATED, configs.API_ERROR, 
                configs.UNKNOWN_ERROR, configs.MAX_RETRIES)
    data_collection.write_collected_data_in_json(projects, collection_path)
    projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
    data_collection.compile_and_execute_microbenchmarks_for_all_projects(projects, configs.GENERATED_MICROBENCHMARKS_DIR, 
                configs.CODE_NOT_GENERATED, configs.API_ERROR, configs.UNKNOWN_ERROR, configs.PACKAGE_NAME, collection_path)

if __name__ == "__main__":
    main()