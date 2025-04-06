import configs
import clone
import static_analysis
import microbenchmarks_creation
import project_configuration
import data_collection
import utils

def main():
    projects = configs.PROJECTS_INFO
    clone.clone_projects(configs.PROJECTS_PATH, configs.PROJECTS_INFO)
    project_configuration.configure_projects(configs.PROJECTS_INFO, configs.JMH_POM_TEMPLATE)
    static_analysis.run_analysis_on_projects(configs.PROJECTS_INFO)
    microbenchmarks_creation.create_microbenchmarks(configs.PROJECTS_INFO, configs.PROMPT_ONE, configs.API_KEY, 
                configs.INTERFACE_FOUND, configs.ABSTRACT_CLASS_FOUND, configs.CODE_NOT_GENERATED, configs.API_ERROR, configs.UNKNOWN_ERROR, configs.MAX_RETRIES)
    data_collection.write_collected_data_in_json(configs.PROJECTS_INFO, configs.DATA_COLLECTION_PATH, configs.CODE_NOT_GENERATED)
    # projects = utils.read_projects(configs.DATA_COLLECTION_PATH, configs.PROJECT_NAMES)
    data_collection.compile_microbenchmarks_for_all_projects(projects, configs.GENERATED_MICROBENCHMARKS_DIR, 
                configs.ABSTRACT_CLASS_FOUND, configs.INTERFACE_FOUND, configs.CODE_NOT_GENERATED, configs.API_ERROR, configs.UNKNOWN_ERROR)

if __name__ == "__main__":
    main()