import configs
import clone
import static_analysis
import microbenchmarks_creation
import project_configuration
import data_collection
import utils
import data_analysis
import argparse

def main():
    projects = configs.PROJECTS_INFO
    collection_path = configs.DATA_COLLECTION_PATH
    parser = argparse.ArgumentParser()
    prompt = configs.PROMPT_THREE

    parser.add_argument("-c", "--config", action="store_true", help="This command runs configuration functions")
    parser.add_argument("-s", "--static-analysis", action="store_true", help="This command runs static analysis on the projects")
    parser.add_argument("-m", "--microbenchmarks-creation", action="store_true", help="This command creates microbenchmarks for the projects")
    parser.add_argument("-d", "--data-collection", action="store_true", help="This command collects compilation, execution, and statement coverage data from generated microbenchmarks")
    parser.add_argument("-a", "--analysis", action="store_true", help="This command analyzes collected data")
    parser.add_argument("-p", "--projects-to-ignore", nargs='+', default=[], help="This command takes a list of projects to ignore during data collection")
    parser.add_argument("-b", "--benchmark-analysis", action="store_true", help="This command runs benchmark analysis on the projects")
    parser.add_argument("-j", "--jacoco-coverage", action="store_true", help="This command runs jacoco coverage analysis on the projects that have human-written jmh microbenchmarks")
    parser.add_argument("-u", "--update-projects", action="store_true", help="This command updates the projects' dictinoary attributes ad ads new ones from the changes made to configs.py")
    parser.add_argument("-f-a", "--file-analysis", action="store_true", help="This command runs the final analaysis on all the runs of data that have been collected")

    args = parser.parse_args()

    if args.update_projects:
        print("Updating projects...")
        projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
        utils.update_projects_attributes(projects, configs.PROJECTS_INFO)
        data_collection.write_collected_data_in_json(projects, collection_path)

    if args.config:
        for project in projects:
            if project["name"] == "RxJava":
                project["java_version"] = "17.0.14-tem"
        clone.clone_projects(configs.PROJECTS_PATH, projects, configs.GENERATED_MICROBENCHMARKS_DIR)
        project_configuration.configure_projects(projects, configs.JMH_POM_TEMPLATE, configs.GENERATED_MICROBENCHMARKS_DIR)

    if args.static_analysis:
        static_analysis.run_analysis_on_projects(projects)
        data_collection.write_collected_data_in_json(projects, collection_path)

    if args.benchmark_analysis:
        projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
        projects = static_analysis.gather_project_jmh_data(projects)
        data_collection.write_collected_data_in_json(projects, collection_path)

    if args.microbenchmarks_creation:
        projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
        microbenchmarks_creation.create_microbenchmarks(projects, prompt, configs.API_KEY, 
                    configs.INTERFACE_FOUND, configs.ABSTRACT_CLASS_FOUND, configs.CODE_NOT_GENERATED, configs.API_ERROR, 
                    configs.UNKNOWN_ERROR, configs.MAX_RETRIES)
        data_collection.write_collected_data_in_json(projects, collection_path)

    if args.data_collection:
        projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
        data_collection.compile_and_execute_microbenchmarks_for_all_projects(projects, configs.GENERATED_MICROBENCHMARKS_DIR, 
                    configs.CODE_NOT_GENERATED, configs.API_ERROR, configs.UNKNOWN_ERROR, configs.PACKAGE_NAME, collection_path, 
                    configs.LIST_OF_COMPILE_ERRORS, args.projects_to_ignore)
        data_collection.write_collected_data_in_json(projects, collection_path)
    
    if args.jacoco_coverage:
        projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
        data_collection.collect_coverage_on_projects_with_jmh(projects, configs.GENERATED_MICROBENCHMARKS_DIR, args.projects_to_ignore, configs.PACKAGE_NAME)

    if args.analysis:
        projects = utils.read_projects(collection_path, configs.PROJECT_NAMES)
        data_analysis.find_most_frequent_compile_errors(projects, configs.LIST_OF_COMPILE_ERRORS)

    if args.file_analysis:
        projects = utils.read_all_data_runs(configs.FINAL_DATA_RUN_PATHS, configs.PROJECT_NAMES, configs.DATA_COMPACT_PATH)
        data_analysis.calc_stat_on_data(projects, configs.NUM_OF_RUNS, configs.FINAL_ANALYSIS_PATH)


if __name__ == "__main__":
    main()