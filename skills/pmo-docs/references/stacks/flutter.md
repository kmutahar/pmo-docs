---
playbook_version: 1
---
Detected by: pubspec.yaml with dependencies containing "flutter"
Checked against: Flutter 3.47, Navigation and routing, Fetch data from the internet, State management, An introduction to widget testing, 2026-11-11
Unverified: auto_route, GoRoute, --dart-define keys, dio and retrofit, drift, sqflite and hive paths

# Flutter

A cross-platform framework for building client applications across mobile, web and desktop.

## Routes, pages or screens
- **Look in:** lib/screens/, lib/pages/, lib/features/, lib/routes/, lib/main.dart
- **Read:** MaterialApp (routes, onGenerateRoute), GoRoute, auto_route, Navigator.push, screen widgets, path:line
- **Record as:** the screens and client calls table of the document being drafted, each with path:line

## Data models
- **Look in:** lib/models/, lib/entities/, *.g.dart, local storage schemas (drift, sqflite, hive)
- **Read:** Dart model classes, freezed, json_serializable annotations, fields, relations and states
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** android/app/src/main/AndroidManifest.xml, ios/Runner/Info.plist, lib/auth/, lib/services/
- **Read:** platform permissions (uses-permission, Info.plist usage descriptions), app role checks, token storage
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** pubspec.yaml, lib/config/, lib/firebase_options.dart, --dart-define keys, .env*
- **Read:** configuration keys, flavor names, environment variable names, never secret values; defined environments
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** test/, integration_test/, test/**/*.dart (flutter_test, integration_test)
- **Read:** testWidgets, test methods, pumpWidget calls, screen and unit assertions
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** inspect client calls in dio, http, retrofit; backend OpenAPI spec is source of truth
- **Without running:** read backend endpoint calls found in code and say the list was read from the code, not run
