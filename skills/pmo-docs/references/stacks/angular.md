---
playbook_version: 1
---
Detected by: angular.json or package.json dependencies containing "@angular/core"
Checked against: Angular 22, Angular Routing, Control route access with guards, Understanding communication with backend services using HTTP, Interceptors, Configuring application environments, Unit testing, 2026-11-26
Unverified: app.routes.ts file naming, HttpInterceptorFn symbol name, TestBed usage and E2E test tools (Playwright, Cypress)

# Angular

A TypeScript frontend framework for structured single-page and SSR web applications.

## Routes, pages or screens
- **Look in:** src/app/**/*.routes.ts, src/app/**/*-routing.module.ts, src/app/**/*.component.ts
- **Read:** Routes arrays, path and children definitions, lazy-loaded routes/components, routed components, path:line
- **Record as:** the screens and client calls table of the document being drafted, each with path:line

## Data models
- **Look in:** src/app/**/models/, src/app/**/interfaces/, src/app/**/*.model.ts
- **Read:** TypeScript interfaces, types, classes, fields, relations and enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** src/app/**/guards/, src/app/**/interceptors/, route canActivate/canMatch properties
- **Read:** CanActivateFn/CanMatchFn route guards, HTTP auth interceptors (withInterceptors), role checks and role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** angular.json (configurations and fileReplacements), src/environments/environment*.ts
- **Read:** environment keys and API base URL names; defined environments; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** src/**/*.spec.ts, e2e/ (Vitest, Karma/Jasmine, ng test)
- **Read:** describe/it blocks, component and service assertions, tested screens and API calls
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** no command to run; read HttpClient calls in services (the backend OpenAPI spec is the source of truth)
- **Without running:** read backend endpoint calls found in code and say the list was read from the code, not run
