from dotenv import load_dotenv
import os

load_dotenv()

JMH_POM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>

<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <groupId>org.ai.bench.jmh.generated</groupId>
    <artifactId>generated_jmh</artifactId>
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
        <sourceDirectory>src/jmh/java</sourceDirectory>
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

API_KEY = os.getenv("GPT_KEY")

PROJECTS_INFO = [
    {
        "name": "logging-log4j2",
        "ssh_url": "git@github.com:apache/logging-log4j2.git",
        "root_path": os.path.join("..", "projects", "logging-log4j2"),
        "analysis_path": os.path.join("..", "projects", "logging-log4j2", "log4j-core", "src", "main", "java", "org", "apache", "logging", "log4j", "core"),
        "modules": [],
        "has_maven": True,
        "parent_pom_path": os.path.join("..", "projects", "logging-log4j2", "log4j-parent", "pom.xml"),
        "dependency_list": [
            {
                "artifactId": "log4j-core",
                "groupId": "org.apache.logging.log4j",
                "version": "${revision}"
            },
            {
                "artifactId": "log4j-api",
                "groupId": "org.apache.logging.log4j",
                "version": "${revision}"
            }
        ]
    },
    {
        "name": "kafka",
        "ssh_url": "git@github.com:apache/kafka.git",
        "root_path": os.path.join("..", "projects", "kafka"),
        "analysis_path": os.path.join("..", "projects", "kafka", "core", "src", "main", "java", "kafka", "server"),
        "has_maven": False,
        "modules": [],
        "gradle_settings_path": os.path.join("..", "projects", "kafka", "settings.gradle")
    },
    {
        "name": "RxJava",
        "ssh_url": "git@github.com:ReactiveX/RxJava.git",
        "root_path": os.path.join("..", "projects", "RxJava"),
        "analysis_path": os.path.join("..", "projects", "RxJava", "src", "main", "java", "io", "reactivex", "rxjava3"),
        "has_maven": False,
        "modules": [],
        "gradle_settings_path": os.path.join("..", "projects", "RxJava", "settings.gradle")
    },
    {
        "name": "Java",
        "ssh_url": "git@github.com:TheAlgorithms/Java.git",
        "root_path": os.path.join("..", "projects", "Java"),
        "analysis_path": os.path.join("..", "projects", "Java", "src", "main", "java", "com", "thealgorithms"),
        "modules": [],
        "has_maven": True,
        "parent_pom_path": os.path.join("..", "projects", "Java", "pom.xml")
    },
    {
        "name": "gson",
        "ssh_url": "git@github.com:google/gson.git",
        "root_path": os.path.join("..", "projects", "gson"),
        "analysis_path": os.path.join("..", "projects", "gson", "gson", "src", "main", "java", "com", "google", "gson"),
        "modules": [],
        "has_maven": True,
        "parent_pom_path": os.path.join("..", "projects", "gson", "pom.xml"),
        "dependency_list": [
            {
                "artifactId": "proguard-core",
                "groupId": "com.guardsquare",
                "version": "9.1.9"
            },
            {
                "artifactId": "proguard-base",
                "groupId": "com.guardsquare",
                "version": "7.6.1"
            }
        ]
    },
    {
        "name": "jjwt",
        "ssh_url": "git@github.com:jwtk/jjwt.git",
        "root_path": os.path.join("..", "projects", "jjwt"),
        "analysis_path": os.path.join("..", "projects", "jjwt", "impl", "src", "main", "java", "io", "jsonwebtoken", "impl"),
        "modules": [],
        "has_maven": True,
        "parent_pom_path": os.path.join("..", "projects", "jjwt", "pom.xml")
    }
]

PROJECTS_PATH = os.path.join("..", "projects")
DATA_COLLECTION_PATH = os.path.join("..", "data", "collected")
GENERATED_MICROBENCHMARKS_DIR = "generated_jmh"
CODE_NOT_GENERATED = "Code not generated"
INTERFACE_FOUND = "Interface found"
ABSTRACT_CLASS_FOUND = "Abstract class found"
UNKNOWN_ERROR = "Unknown error"
API_ERROR = "API error"
PROJECT_NAMES = [project["name"] for project in PROJECTS_INFO]
MAX_RETRIES = 5

PROMPT_ONE = f"""You are a senior verification developer. You are an expert in
writing JMH microbenchmark test cases. You are also an expert analyzing code and writing JMH test cases for it.
You are proficient in the Java programming language. You are assigned to write an appropriate
number of JMH microbenchmark test cases to test the performance of the following code module. Please only provide the the benchmark module
and no explanations. You must ignore "Abstract classes" by returning "{ABSTRACT_CLASS_FOUND}" as output. 
You must ignore "interfaces" by returning "{INTERFACE_FOUND}" as output.

Here is the code:\n\n"""