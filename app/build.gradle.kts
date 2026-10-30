plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "ch.chesstour.app"
    compileSdk = 35
    defaultConfig {
        applicationId = "ch.chesstour.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 5
        versionName = "0.5"
    }
}
