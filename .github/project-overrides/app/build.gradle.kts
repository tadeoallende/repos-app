import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.parcelize)
}

val localProps = Properties().apply {
    rootProject.file("local.properties").takeIf { it.exists() }?.inputStream()?.use(::load)
}
fun prop(name: String, default: String = ""): String =
    listOf(localProps.getProperty(name), providers.gradleProperty(name).orNull)
        .firstOrNull { !it.isNullOrBlank() } ?: default

android {
    namespace = "com.angulismotv"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.angulismotv"
        minSdk = 21
        targetSdk = 34
        versionCode = 10
        versionName = "1.9"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        buildConfigField("String", "IPTV_ORG_URL", "\"${prop("IPTV_ORG_URL", "https://iptv-org.github.io/iptv/index.m3u")}\"")
        buildConfigField("String", "REMOTE_SOURCES_CONFIG_URL", "\"${prop("REMOTE_SOURCES_CONFIG_URL", "https://raw.githubusercontent.com/tadeoallende/repos-app/refs/heads/main/fuentes.json")}\"")
        buildConfigField("String", "CHANNELS_URL", "\"${prop("CHANNELS_URL")}\"")
        buildConfigField("String", "EVENTS_URL", "\"${prop("EVENTS_URL")}\"")
        buildConfigField("String", "CUSTOM_CHANNELS_URL", "\"${prop("CUSTOM_CHANNELS_URL", "https://raw.githubusercontent.com/tadeoallende/repos-app/refs/heads/main/canales.json")}\"")
        buildConfigField("String", "UPDATE_URL", "\"${prop("UPDATE_URL")}\"")
        buildConfigField("String", "WEB_BASE_URL", "\"${prop("WEB_BASE_URL", "https://angulismotv.pages.dev")}\"")
    }

    signingConfigs {
        if (prop("RELEASE_STORE_FILE").isNotEmpty()) {
            create("release") {
                storeFile = rootProject.file(prop("RELEASE_STORE_FILE"))
                storePassword = prop("RELEASE_STORE_PASSWORD")
                keyAlias = prop("RELEASE_KEY_ALIAS")
                keyPassword = prop("RELEASE_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfigs.findByName("release")?.let { signingConfig = it }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    buildFeatures {
        viewBinding = true
        buildConfig = true
    }
}

dependencies {
    implementation(libs.bundles.android.ui)
    implementation(libs.bundles.media.playback)
    implementation(libs.bundles.network.json)
    implementation(libs.bundles.cast)
    implementation(libs.glide)
    testImplementation(libs.bundles.unit.testing)
    androidTestImplementation(libs.bundles.instrumentation.testing)
}
