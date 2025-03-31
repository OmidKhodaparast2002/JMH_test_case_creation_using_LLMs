import utils
from dotenv import load_dotenv
import os
import time

load_dotenv()

JMH_POM_XML = """
<?xml version="1.0" encoding="UTF-8"?>

<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <groupId>org.ai.bench.jmh</groupId>
    <artifactId>ai-bench-jmh</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <name>LLM-created-JMH-microbenchmarks</name>

    <prerequisites>
        <maven>3.0</maven>
    </prerequisites>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jmh.version>1.13</jmh.version>
        <javac.target>21</javac.target>
        <uberjar.name>benchmarks</uberjar.name>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.openjdk.jmh</groupId>
            <artifactId>jmh-core</artifactId>
            <version>${jmh.version}</version>
        </dependency>
        <dependency>
            <groupId>org.openjdk.jmh</groupId>
            <artifactId>jmh-generator-annprocess</artifactId>
            <version>${jmh.version}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>commons-lang</groupId>
            <artifactId>commons-lang</artifactId>
            <version>2.6</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.1</version>
                <configuration>
                    <compilerVersion>${javac.target}</compilerVersion>
                    <source>${javac.target}</source>
                    <target>${javac.target}</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>2.2</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <finalName>${uberjar.name}</finalName>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>org.openjdk.jmh.Main</mainClass>
                                </transformer>
                            </transformers>
                            <filters>
                                <filter>
                                    <!--
                                        Shading signed JARs will fail without this.
                                        http://stackoverflow.com/questions/999489/invalid-signature-file-when-attempting-to-run-a-jar
                                    -->
                                    <artifact>*:*</artifact>
                                    <excludes>
                                        <exclude>META-INF/*.SF</exclude>
                                        <exclude>META-INF/*.DSA</exclude>
                                        <exclude>META-INF/*.RSA</exclude>
                                    </excludes>
                                </filter>
                            </filters>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
        <pluginManagement>
            <plugins>
                <plugin>
                    <artifactId>maven-clean-plugin</artifactId>
                    <version>2.5</version>
                </plugin>
                <plugin>
                    <artifactId>maven-deploy-plugin</artifactId>
                    <version>2.8.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-install-plugin</artifactId>
                    <version>2.5.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-jar-plugin</artifactId>
                    <version>2.4</version>
                </plugin>
                <plugin>
                    <artifactId>maven-javadoc-plugin</artifactId>
                    <version>2.9.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-resources-plugin</artifactId>
                    <version>2.6</version>
                </plugin>
                <plugin>
                    <artifactId>maven-site-plugin</artifactId>
                    <version>3.3</version>
                </plugin>
                <plugin>
                    <artifactId>maven-source-plugin</artifactId>
                    <version>2.2.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>2.17</version>
                </plugin>
            </plugins>
        </pluginManagement>
    </build>
</project>"""

GPT_KEY = os.getenv("GPT_KEY")

PROJECT_INFO = [
    {
        "name": "logging-log4j2",
        "ssh_url": "git@github.com:apache/logging-log4j2.git",
        "analysis_path": "../projects/logging-log4j2/log4j-core/src/main/java/org/apache/logging/log4j/core",
        "modules": [],
        "has_maven": True,
        "parent_pom_path": "../projects/logging-log4j2/log4j-perf-test/pom.xml"
    },
    {
        "name": "kafka",
        "ssh_url": "git@github.com:apache/kafka.git",
        "analysis_path": "../projects/kafka/core/src/main/java/kafka/server",
        "modules": []
    },
    {
        "name": "RxJava",
        "ssh_url": "git@github.com:ReactiveX/RxJava.git",
        "analysis_path": "../projects/RxJava/src/main/java/io/reactivex/rxjava3",
        "modules": []
    },
    {
        "name": "Java",
        "ssh_url": "git@github.com:TheAlgorithms/Java.git",
        "analysis_path": "../projects/Java/src/main/java/com/thealgorithms",
        "modules": [],
        "has_maven": True,
        "parent_pom_path": "../projects/Java/pom.xml"
    },
    {
        "name": "gson",
        "ssh_url": "git@github.com:google/gson.git",
        "analysis_path": "../projects/gson/gson/src/main/java/com/google/gson",
        "modules": [],
        "has_maven": True,
        "parent_pom_path": "../projects/gson/gson/pom.xml"
    },
    {
        "name": "jjwt",
        "ssh_url": "git@github.com:jwtk/jjwt.git",
        "analysis_path": "../projects/jjwt/impl/src/main/java/io/jsonwebtoken/impl",
        "modules": [],
        "has_maven": True,
        "parent_pom_path": "../projects/jjwt/impl/pom.xml"
    }
]

PROJECTS_PATH = "../projects"
DATA_COLLECTION_PATH = "../data/collected"

MAX_RETRIES = 5

PROMPT_TEXT_ONE = """You are a senior verification developer. You are an expert in
writing JMH microbenchmark test cases. You are also an expert analyzing code and writing JMH test cases for it.
You are proficient in the Java programming language. You are assigned to write an appropriate
number of JMH microbenchmark test cases to test the performance of the following code module. Please only provide the the benchmark module
and no explanations. You must ignore "Abstract classes" and "Interfaces":\n\n"""

def main():
    if not utils.folder_exists(PROJECTS_PATH):
        utils.create_folder(PROJECTS_PATH)
        for project in PROJECT_INFO:
            utils.clone(project["ssh_url"], PROJECTS_PATH)

    for project in PROJECT_INFO:
        utils.run_analysis(project, project["analysis_path"])

    curr_timestamp = time.time()
    requests = 0
    
    for project in PROJECT_INFO:
        tokens = 0
        for module in project["modules"]:
            prompt = PROMPT_TEXT_ONE + module["code"]

            if time.time() - curr_timestamp > 60:
                curr_timestamp = time.time()

            requests += 1
            tokens = len(prompt) // 4 + tokens
            if tokens > 250000 and time.time() - curr_timestamp < 60:
                print("TPM exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                tokens = 0
            if requests > 1000 and time.time() - curr_timestamp < 60:
                print("RPM exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                requests = 0

            try:
                tests = utils.prompt_llm(prompt, GPT_KEY, MAX_RETRIES)
                module["test_code"] = tests
            except utils.NoCodeFoundError as e:
                print(e)
                module["test_code"] = "Code not found"
            except utils.APIError as e:
                print(e)
                module["test_code"] = "API error"
            except Exception as e:
                print(e)
                module["test_code"] = "Error"
    
    for project in PROJECT_INFO:
        if not utils.folder_exists(DATA_COLLECTION_PATH):
            utils.create_folder(DATA_COLLECTION_PATH)
        utils.write_json(project, f"{DATA_COLLECTION_PATH}/{project['name']}.json")
            

if __name__ == "__main__":
    main()