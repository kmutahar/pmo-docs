---
playbook_version: 1
---
Detected by: *.xcodeproj, *.xcworkspace or Package.swift containing SwiftUI or UIKit targets
Checked against: Swift 6.4, Navigation (SwiftUI), SwiftData, Information Property List, Swift Testing, XCTest, URLSession, 2026-11-26
Unverified: UIKit navigation patterns, Core Data .xcdatamodeld paths, .xcconfig conventions, Alamofire and Keychain wrapper names

# iOS (Swift)

A native Apple client application written in Swift with SwiftUI or UIKit.

## Routes, pages or screens
- **Look in:** Sources/, */Views/, */Screens/, */Navigation/, *App.swift
- **Read:** NavigationStack/NavigationSplitView destinations, TabView tabs, UIViewController flows, screen views, path:line
- **Record as:** the screens and client calls table of the document being drafted, each with path:line

## Data models
- **Look in:** */Models/, */Data/, *.xcdatamodeld
- **Read:** SwiftData @Model classes, Codable structs, Core Data entities, fields, relations and enum states
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** Info.plist, *.entitlements, */Auth/, */Services/
- **Read:** Info.plist privacy usage descriptions (NS*UsageDescription), entitlements, auth/session managers and role checks
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** Info.plist, *.xcconfig, Xcode schemes (*.xcscheme)
- **Read:** build configurations (Debug, Release, custom schemes) and config key names; defined environments; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** *Tests/, *UITests/ (Swift Testing @Test, XCTest XCTestCase)
- **Read:** @Test functions and test* methods, view/service assertions, covered flows
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** no command to run; read the client calls in URLSession or Alamofire (the backend OpenAPI spec is the source of truth)
- **Without running:** read backend endpoint calls found in code and say the list was read from the code, not run
