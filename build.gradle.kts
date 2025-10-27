plugins {
    id("com.diffplug.spotless") version "6.23.3"
}
configure<com.diffplug.gradle.spotless.SpotlessExtension> {
    kotlinGradle {
        target("**/*.kts")
        ktlint()
    }
    java {
        target("**/*.java")
        googleJavaFormat()
                .reflowLongStrings()
                .skipJavadocFormatting()
                .reorderImports(false)
    }
    yaml {
        target("**/*.yaml")
        targetExclude("**/.gradle/**", "codespace/chart/**", "slurm/chart/**", "**/pnpm-lock.yaml")
        jackson()
                .feature("ORDER_MAP_ENTRIES_BY_KEYS", false)
                .yamlFeature("MINIMIZE_QUOTES", true)
                .yamlFeature("ALWAYS_QUOTE_NUMBERS_AS_STRINGS", true)
                .yamlFeature("SPLIT_LINES", false)
                .yamlFeature("LITERAL_BLOCK_STYLE", true)
    }
    json {
        target("**/*.json")
        targetExclude("**/.gradle/**")
        jackson()
                .feature("ORDER_MAP_ENTRIES_BY_KEYS", true)
    }
    python {
        target("**/*.py")
       targetExclude("**/csst/**", "**/venv/**")
        // black("24.4.2")
    }
}


allprojects {
    repositories {
//        maven { setUrl(System.getenv("MAVEN_CENTRAL_REPOSITORY") ?: "https://mirrors.lab.zverse.space/repository/maven-public/") }
//        maven { setUrl("https://mirrors.lab.zverse.space/repository/maven-releases/") }
        mavenCentral()
    }
    version = "1.0.0"
}
