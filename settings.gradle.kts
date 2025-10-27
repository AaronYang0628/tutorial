rootProject.name = "tutorial"

pluginManagement {
    repositories {
        maven { setUrl(System.getenv("GRADLE_PLUGIN_REPOSITORY") ?: "https://maven.aliyun.com/repository/gradle-plugin") }
        gradlePluginPortal()
        mavenCentral()
    }
}

include("milvus")
include("milvus:java")

include("flink")
