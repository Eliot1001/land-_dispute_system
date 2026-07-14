import java.util.Properties
import java.io.FileInputStream

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

// Build output normally lives at <repo root>/build. On machines where the
// project sits inside a synced folder (OneDrive, Dropbox, etc.), the sync
// client can lock files mid-write and break Gradle's clean/merge tasks. To
// work around that on just this machine, set `flutter.buildDir=<absolute
// path outside the synced folder>` in android/local.properties (gitignored,
// never committed) - everyone else keeps the default relative path.
val localProperties = Properties()
val localPropertiesFile = rootProject.file("local.properties")
if (localPropertiesFile.exists()) {
    FileInputStream(localPropertiesFile).use { localProperties.load(it) }
}
val customBuildDir = localProperties.getProperty("flutter.buildDir")

val newBuildDir: Directory =
    if (customBuildDir != null) {
        rootProject.layout.projectDirectory.dir(customBuildDir)
    } else {
        rootProject.layout.buildDirectory.dir("../../build").get()
    }
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
