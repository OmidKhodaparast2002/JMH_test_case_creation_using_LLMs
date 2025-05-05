from dotenv import load_dotenv
import os

load_dotenv()

GENERATED_MICROBENCHMARKS_DIR = "generated_jmh"
PACKAGE_NAME = "org.ai.bench.jmh.generated"
JMH_POM_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8"?>

<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <groupId>org.ai.bench.jmh.generated</groupId>
    <artifactId>{GENERATED_MICROBENCHMARKS_DIR}</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <name>LLM-created-JMH-microbenchmarks</name>

    <prerequisites>
        <maven>3.0</maven>
    </prerequisites>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jmh.version>1.37</jmh.version>
        <uberjar.name>{GENERATED_MICROBENCHMARKS_DIR}</uberjar.name>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.openjdk.jmh</groupId>
            <artifactId>jmh-core</artifactId>
            <version>${{jmh.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.openjdk.jmh</groupId>
            <artifactId>jmh-generator-annprocess</artifactId>
            <version>${{jmh.version}}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>commons-lang</groupId>
            <artifactId>commons-lang</artifactId>
            <version>2.6</version>
        </dependency>
    </dependencies>

    <repositories>
        <repository>
            <releases>
                <enabled>false</enabled>
            </releases>
            <snapshots>
                <enabled>true</enabled>
            </snapshots>
            <id>apache.snapshots</id>
            <url>https://repository.apache.org/snapshots</url>
        </repository>
    </repositories>

    <build>
        <sourceDirectory>src/jmh/java</sourceDirectory>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>${{javac.target}}</source>
                    <target>${{javac.target}}</target>
                    <annotationProcessorPaths combine.children="append">
                        <path>
                            <groupId>org.openjdk.jmh</groupId>
                            <artifactId>jmh-generator-annprocess</artifactId>
                            <version>${{jmh.version}}</version>
                        </path>
                    </annotationProcessorPaths>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.4.1</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <finalName>${{uberjar.name}}</finalName>
                            <transformers combine.children="append">
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>org.openjdk.jmh.Main</mainClass>
                                </transformer>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ServicesResourceTransformer" />
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
                    <version>3.4.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-deploy-plugin</artifactId>
                    <version>3.1.4</version>
                </plugin>
                <plugin>
                    <artifactId>maven-install-plugin</artifactId>
                    <version>3.1.4</version>
                </plugin>
                <plugin>
                    <artifactId>maven-jar-plugin</artifactId>
                    <version>3.3.0</version>
                </plugin>
                <plugin>
                    <artifactId>maven-javadoc-plugin</artifactId>
                    <version>3.11.2</version>
                </plugin>
                <plugin>
                    <artifactId>maven-resources-plugin</artifactId>
                    <version>3.3.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-site-plugin</artifactId>
                    <version>3.21.0</version>
                </plugin>
                <plugin>
                    <artifactId>maven-source-plugin</artifactId>
                    <version>3.3.1</version>
                </plugin>
                <plugin>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>3.5.3</version>
                </plugin>
            </plugins>
        </pluginManagement>
    </build>
</project>"""

API_KEY = os.getenv("GPT_KEY")

PROJECTS_INFO = [
    {
        "name": "logging-log4j2",
        "ssh_url": "https://github.com/apache/logging-log4j2.git",
        "root_path": os.path.join("..", "projects", "logging-log4j2"),
        "analysis_path": os.path.join("..", "projects", "logging-log4j2", "log4j-core", "src", "main", "java", "org", "apache", "logging", "log4j", "core"),
        "modules": [],
        "has_maven": True,
        "has_jmh": True,
        "jmh_path": os.path.join("..", "projects", "logging-log4j2", "log4j-perf-test", "src", "main", "java", "org", "apache", "logging", "log4j", "perf"),
        "maven_install_dirs": [
            os.path.join("..", "projects", "logging-log4j2"),
        ],
        "parent_pom_path": os.path.join("..", "projects", "logging-log4j2", "log4j-parent", "pom.xml"),
        "dependency_list": [
            {
                "artifactId": "log4j-core",
                "groupId": "org.apache.logging.log4j",
                "version": "2.25.0-SNAPSHOT"
            },
            {
                "artifactId": "log4j-api",
                "groupId": "org.apache.logging.log4j",
                "version": "2.25.0-SNAPSHOT"
            }
        ],
        "java_version": "17.0.14-tem"
    },
    {
        "name": "kafka",
        "ssh_url": "https://github.com/apache/kafka.git",
        "root_path": os.path.join("..", "projects", "kafka"),
        "analysis_path": os.path.join("..", "projects", "kafka", "clients", "src", "main", "java", "org", "apache", "kafka"),
        "has_maven": False,
        "modules": [],
        "has_jmh": True,
        "jmh_path": os.path.join("..", "projects", "kafka", "jmh-benchmarks", "src", "main", "java", "org", "apache", "kafka", "jmh"),
        "gradle_settings_path": os.path.join("..", "projects", "kafka", "settings.gradle"),
        "java_version": "17.0.14-tem",
        "dependency_list": [
            ":clients"
        ]
    },
    {
        "name": "RxJava",
        "ssh_url": "https://github.com/ReactiveX/RxJava.git",
        "root_path": os.path.join("..", "projects", "RxJava"),
        "analysis_path": os.path.join("..", "projects", "RxJava", "src", "main", "java", "io", "reactivex", "rxjava3"),
        "has_maven": False,
        "modules": [],
        "has_jmh": True,
        "jmh_path": os.path.join("..", "projects", "RxJava", "src", "jmh", "java", "io", "reactivex", "rxjava3"),
        "gradle_settings_path": os.path.join("..", "projects", "RxJava", "settings.gradle"),
        "java_version": "8.0.442-tem",
        "dependency_list": [
            ":"
        ]
    },
    {
        "name": "Java",
        "ssh_url": "https://github.com/TheAlgorithms/Java.git",
        "root_path": os.path.join("..", "projects", "Java"),
        "analysis_path": os.path.join("..", "projects", "Java", "src", "main", "java", "com", "thealgorithms"),
        "modules": [],
        "has_maven": True,
        "has_jmh": False,
        "maven_install_dirs": [
            os.path.join("..", "projects", "Java")
        ],
        "parent_pom_path": os.path.join("..", "projects", "Java", "pom.xml"),
        "dependency_list": [
            {
                "artifactId": "commons-lang3",
                "groupId": "org.apache.commons",
                "version": "3.17.0"
            },
            {
                "artifactId": "commons-collections4",
                "groupId": "org.apache.commons",
                "version": "4.5.0-M3"
            },
            {
                "artifactId": "Java",
                "groupId": "com.thealgorithms",
                "version": "1.0-SNAPSHOT"
            }
        ],
        "java_version": "21.0.6-tem"
    },
    {
        "name": "gson",
        "ssh_url": "https://github.com/google/gson.git",
        "root_path": os.path.join("..", "projects", "gson"),
        "analysis_path": os.path.join("..", "projects", "gson", "gson", "src", "main", "java", "com", "google", "gson"),
        "modules": [],
        "has_maven": True,
        "has_jmh": False,
        "maven_install_dirs": [
            os.path.join("..", "projects", "gson", "gson")
        ],
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
            },
            {
                "artifactId": "gson",
                "groupId": "com.google.code.gson",
                "version": "2.12.2-SNAPSHOT"
            }
        ],
        "java_version": "17.0.14-tem"
    },
    {
        "name": "jjwt",
        "ssh_url": "https://github.com/jwtk/jjwt.git",
        "root_path": os.path.join("..", "projects", "jjwt"),
        "analysis_path": os.path.join("..", "projects", "jjwt", "impl", "src", "main", "java", "io", "jsonwebtoken", "impl"),
        "modules": [],
        "has_maven": True,
        "has_jmh": False,
        "maven_install_dirs": [
            os.path.join("..", "projects", "jjwt")
        ],
        "parent_pom_path": os.path.join("..", "projects", "jjwt", "pom.xml"),
        "dependency_list": [
            {
                "artifactId": "jjwt-api",
                "groupId": "io.jsonwebtoken",
                "version": "0.12.7-SNAPSHOT"
            },
            {
                "artifactId": "jjwt-impl",
                "groupId": "io.jsonwebtoken",
                "version": "0.12.7-SNAPSHOT"
            }
        ],
        "java_version": "17.0.14-tem"
    }
]

PROJECTS_PATH = os.path.join("..", "projects")
DATA_COLLECTION_PATH = os.path.join("..", "data", "collected")
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
and no explanations. You must not create benchmarks for private, protected, and default methods and classes.

Here is the code:\n\n"""

PROMPT_TWO = f"""You are a senior verification developer. You are an expert in
writing JMH microbenchmark test cases. You are also an expert analyzing code and writing JMH test cases for it.
You are proficient in the Java programming language and write valid Java code with no errors. You are assigned to write an appropriate
number of JMH microbenchmark test cases to test the performance of the following code module. Please only provide the the benchmark module
and no explanations. You must not create benchmarks for private, protected, and default methods and classes. Please make sure you have all necessary imports.
Moreover, make sure to import the module for which you are writing a JMH microbenchmark test cases.

Here is the code:\n\n"""

PROMPT_THREE = f"""You are a senior verification developer. You are an expert in
writing JMH microbenchmark test cases. You are also an expert analyzing code and writing JMH test cases for it.
You are proficient in the Java programming language and write valid Java code with no errors. You are assigned to write an appropriate
number of JMH microbenchmark test cases to test the performance of the following code module:

please apply the following instructions while writing the test cases:
-       do not create benchmarks for private, protected, and default methods and classes
-       please import all the import that the modules uses, and all imports needed for the test case to compile and run correctly
-       please make sure you import the module for which you are writing a JMH microbenchmark test cases
-       please do not write a package statement.
-       please make sure you write valid Java code with no syntax errors.
-       In the output, please only provide the code that you have written and no explanations.

Here is the code:\n\n"""

LIST_OF_COMPILE_ERRORS = [
    r"cannot find symbol",
    r"method does not override.*supertype",
    r"incompatible types",
    r"package\s+[\w\.]+\s+does not exist",
    r"class, interface, or enum expected",
    r"illegal start of type",
    r"reached end of file while parsing",
    r"missing return statement",
    r"unclosed string literal",
    r"variable might not have been initialized",
    r"cannot be applied to given types",
    r"constructor .* is undefined|constructor not defined",
    r"no suitable constructor found",
    r"array required but.*found",
    r"inconvertible types",
    r"unexpected type",
    r"non-static variable .* cannot be referenced from a static context",
    r"unreachable statement",
    r"illegal start of expression",
    r"modifier static not allowed here",
    r"enum types may not be instantiated",
    r"reference to variable .* is ambiguous",
    r"class, interface, enum, or record expected",
    r"has private access",
    r"has protected access",
    r"has default access",
    r"annotation type not applicable",
    r"';' expected",
    r"'{' expected",
    r"'}' expected",
    r"'\)' expected",
    r"'\(' expected",
    r"class expected",
    r"expression expected",
    r"not a statement",
    r"invalid method declaration",
    r".*identifier.* expected",
    r"unexpected token",
    r"unclosed character literal",
    r"Must have a class or method signature",
    r"annotation only supports public classes",
    r"annotation is missing a default value",
    r"unreported exception .* must be caught or declared to be thrown",
    r"is not abstract and does not override abstract method .*",
    r"unreported exception .* in default constructor",
    r"Method parameters should be either @State classes or one of special JMH classes",
    r"Field .* is declared within a class not having @State annotation",
    r"is abstract; cannot be instantiated",
    r"a type with the same simple name is already defined",
    r"void cannot be dereferenced",
    r"cannot be accessed from outside package",
    r"is not within bounds of type-variable",
    r".*void.* type not allowed",
    r"expression not allowed as annotation value",
]















"""
'(' expected,
class should be declared in file,
not a statement,
'.' expected,
class, enum or interface expected,
not abstract,
'.class' expected,
classname not enclosing class,
not accessible,
';' missing,
Comparable cannot be inherited,
not found in import,
';' expected,
constructor calls overridden method,
not initialised,
'=' expected,
constructor used as method,
operator '+'
'[' expected,
duplicate class,
operator '||'
already defined,
duplicate methods,
package does not exist,
ambiguous class,
enum as identifier,
permission denied,
array not initialised,
error while writing,
possible loss of precision,
attempt to reference,
Exception never thrown,
public class should be in file,
attempt to rename,
final parameter may not be assigned,
reached end of file while parsing,
bad class file,
generic array creation,
recompile with -Xlint:unchecked,
blank final,
identifier expected,
redefined method,
boolean dereferenced,
illegal character,
reference ambiguous,
bound mismatch,
illegal escape,
repeated modifier,
cannot find symbol,
illegal forward reference,
return in constructor,
attempting weaker access,
illegal reference to static,
return outside method,
does not throw,
illegal start,
return required,
incompatible return type,
impotent setters,
serialVersionUID required,
cannot resolve constructor,
incompatible type,
should be declared in file,
cannot resolve symbol,
instance not accessible,
statement expected,
invalid declaration,
static field should be accessed in a static way
invalid flag,
static not valid on constructor,
cannot use operator,
invalid label,
superclass not found,
can’t access class,
invalid method,
suspicious shadowing,
can’t be applied,
invalid type,
Tag @see: not found
can’t be dereferenced,
javac is not a … command,
type can’t be private,
can’t be instantiated,
main must be static void,
type can’t be widened,
can’t convert from Object,
method cannot hide,
type expected,
can’t delete jar file,
method clone not visible,
type safety,
can’t determine application home,
method matches constructor name,
type safety: type erased,
can’t instantiate abstract class,
method not found,
unable to resolve class,
can’t make static reference,
misplaced construct,
unchecked cast,
capitalisation errors,
misplaced package,
unchecked conversion,
case fallthru,
missing init,
unclosed character literal,
char cannot be dereferenced,
missing method body,
unclosed String literal,
clashes with package,
missing public,	
undefined reference to main,
class expected,	
missing return statement,	
undefined variable,
class has wrong version,
missing variable initialiser,	
unexpected symbols,
class must be defined in a file,
modifier synchronized not allowed,
unqualified enumeration required,
class names only accepted for annotation,
name of constructor mismatch,
unreachable statement,
class names 'unchecked' only accepted,
no field,	
unsorted switch,
class not found,
no method found,
void type,	
no method matching,	
weaker access,
non-final variable,
'{' expected,
class or interface declaration expected,
non-static can’t be referenced,
'}' expected
"""