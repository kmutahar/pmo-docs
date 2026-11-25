---
playbook_version: 1
---
Detected by: go.mod (with net/http handlers or router imports such as gin, chi, echo or fiber)
Checked against: Go 1.27, net/http, testing, Gin 1.12, Chi 5.5, Echo 5.4, 2026-11-26
Unverified: GORM, sqlc, Ent and Fiber conventions, OpenAPI generation tools (swag, oapi-codegen)

# Go

A statically typed language for HTTP services using net/http or routers such as Gin, Chi, Echo and Fiber.

## Routes, pages or screens
- **Look in:** cmd/, internal/, pkg/, router/ or routes/ files, main.go
- **Read:** http.HandleFunc, ServeMux Handle/HandleFunc patterns, router.GET/POST/PUT/PATCH/DELETE, route groups, handler functions, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** internal/model/, models/, domain/, db/migrations/, sqlc.yaml, ent/schema/
- **Read:** Go structs with json/db tags, ORM or sqlc models, foreign-key relations, status constants and enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** internal/middleware/, middleware/, auth/
- **Read:** HTTP middleware wrappers, context user/claims extraction, role or scope checks, role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** internal/config/, config/, .env.example, .env.sample, .env.template, os.Getenv / os.LookupEnv calls
- **Read:** config struct fields and environment variable names; defined environments; read names from the example file only; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** **/*_test.go (testing package, net/http/httptest)
- **Read:** Test* functions, httptest requests, handler and status assertions
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** project OpenAPI spec (docs/swagger.json, openapi.yaml) or swagger endpoint when the service is running
- **Without running:** read the routes found above and say the list was read from the code, not run
