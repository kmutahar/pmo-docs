---
playbook_version: 1
---
Detected by: build.gradle or build.gradle.kts with com.android.application or com.android.library and Kotlin sources
Checked against: Kotlin 2.4, Android 16 (API 36), Android Gradle plugin 9.6, Navigation, Save data in a local database using Room, Permissions on Android, Configure build variants, Fundamentals of testing Android apps, 2026-11-26
Unverified: AndroidManifest.xml uses-permission syntax on the Permissions overview page, src/test and src/androidTest folder names, Retrofit/Ktor client conventions, BuildConfig fields

# Android (Kotlin)

A native Android client application written in Kotlin with Jetpack Compose or Views.

## Routes, pages or screens
- **Look in:** app/src/main/java/**/ui/, app/src/main/java/**/navigation/, app/src/main/res/navigation/
- **Read:** NavHost, NavController, composable destinations, Activity/Fragment entries, screen composables, path:line
- **Record as:** the screens and client calls table of the document being drafted, each with path:line

## Data models
- **Look in:** app/src/main/java/**/data/, app/src/main/java/**/model/, app/src/main/java/**/entity/
- **Read:** Kotlin data classes, Room @Entity/@Dao/@Database definitions, fields, relations and sealed/enum states
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** app/src/main/AndroidManifest.xml, app/src/main/java/**/auth/, app/src/main/java/**/network/
- **Read:** declared Android permissions (uses-permission), runtime permission requests, auth interceptors and role checks
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** app/build.gradle.kts or app/build.gradle, gradle.properties (never open local.properties or keystore properties)
- **Read:** buildTypes, productFlavors, flavorDimensions and config key names; defined environments; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** app/src/test/, app/src/androidTest/ (JUnit, Espresso, Compose UI tests)
- **Read:** @Test functions, screen and ViewModel assertions, covered user flows
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** no command to run; read the client calls in Retrofit, Ktor or OkHttp (the backend OpenAPI spec is the source of truth)
- **Without running:** read backend endpoint calls found in code and say the list was read from the code, not run
