---
playbook_version: 1
---
Detected by: package.json dependencies containing "react-native" or "expo"
Checked against: React Native 0.88 and Expo, Navigating Between Screens, Networking, Testing, Introduction to Expo Router, Environment variables in Expo, Permissions, 2026-11-26
Unverified: React Navigation stack/tab names, Expo Router app/ and _layout conventions, Detox and Maestro test paths, app.config.js/app.json schema details

# React Native

A cross-platform framework for building native mobile apps in React and TypeScript, bare or with Expo.

## Routes, pages or screens
- **Look in:** app/ (Expo Router), src/screens/, screens/, src/navigation/, navigation/
- **Read:** Expo Router screen files and layouts, React Navigation navigators and Screen definitions, screen components, path:line
- **Record as:** the screens and client calls table of the document being drafted, each with path:line

## Data models
- **Look in:** src/models/, src/types/, models/, types/, local storage schemas (WatermelonDB, Realm, SQLite, AsyncStorage)
- **Read:** TypeScript interfaces/types, local database models, fields, relations and lifecycle states
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** app.json, app.config.{js,ts}, android/app/src/main/AndroidManifest.xml, ios/*/Info.plist, src/auth/, src/context/
- **Read:** native permission declarations and usage descriptions, Expo permission requests, auth context/store and role checks
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** app.json, app.config.{js,ts}, eas.json, .env.example, .env.sample, .env.template
- **Read:** environment variable names (EXPO_PUBLIC_ reaches client bundle), build profiles; defined environments; read names from the example file only; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** __tests__/, src/**/*.test.{js,jsx,ts,tsx}, e2e/ (Jest, React Native Testing Library, Detox, Maestro)
- **Read:** test/it blocks, screen render and interaction assertions, covered flows
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** no command to run; read the client calls in fetch, axios or API hooks (the backend OpenAPI spec is the source of truth)
- **Without running:** read backend endpoint calls found in code and say the list was read from the code, not run
