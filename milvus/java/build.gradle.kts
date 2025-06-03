plugins {
    id("java")
}

group = "org.example"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("io.milvus:milvus-sdk-java:2.5.9")
    implementation("org.slf4j:slf4j-api:2.0.9")
    implementation("org.slf4j:slf4j-simple:2.0.9")

    testImplementation(platform("org.junit:junit-bom:5.9.1"))
    testImplementation("org.junit.jupiter:junit-jupiter")
}

tasks.test {
    useJUnitPlatform()
}
