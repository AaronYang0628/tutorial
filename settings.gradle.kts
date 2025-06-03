rootProject.name = "tutorial"

pluginManagement {
    repositories {
        maven { setUrl(System.getenv("GRADLE_PLUGIN_REPOSITORY") ?: "https://maven.aliyun.com/repository/gradle-plugin") }
        gradlePluginPortal()
        mavenCentral()
    }
}

include("milvus")
//include("flink:load-fits-star-catalog")
//include("flink:search-star-catalog")
//include("flink:gaia3:download-as-parquet")
//include("flink:gaia3:parquet-partition")
//include("flink:gaia3:parquet-to-clickhouse")
//include("flink:file-transfer")
//include("flink:fits-to-parquet")
//include("tutorials:service:springboot")
//include("tutorials:monitor:service:springboot")
//include("flink:gaia3:parquet-partition-sort")
//include("flink:ingest-to-es")
//include("metadata:es-sdk")
//include("metadata:es-ingest-job")
//include("metadata:flink-es-ingest-job")
include("milvus:java")
findProject(":milvus:java")?.name = "java"
include("flink")
