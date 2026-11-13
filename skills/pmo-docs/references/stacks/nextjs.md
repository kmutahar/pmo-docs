---
playbook_version: 1
---
Detected by: package.json dependencies containing "next"
Checked against: Next.js 16, Project Structure, Route Handlers, Proxy, Environment Variables, Building your application, 2026-11-11
Unverified: Pages Router paths, auth library file names (auth.ts, lib/auth.*), Prisma and Drizzle locations, test folders

# Next.js

A React framework for full-stack web applications with App Router and Pages Router.

## Routes, pages or screens
- **Look in:** app/**/page.{js,jsx,ts,tsx}, app/**/route.{js,ts}, pages/**/*.{js,jsx,ts,tsx}, optional src/ prefix
- **Read:** route path, URL parameters ([id], [...slug], (group)), HTTP methods, handler, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** prisma/schema.prisma, drizzle/ or schema/ files, models/, types/
- **Read:** model names, field definitions, relation mappings, states and enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** proxy.{js,ts} (named middleware.{js,ts} before Next.js 16), auth.ts, lib/auth.*, Server Actions session checks
- **Read:** how requests are authenticated, role verification logic, role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** next.config.{js,mjs,ts}, .env.example, .env.sample, .env.template
- **Read:** variable and setting names (NEXT_PUBLIC_ reaches browser); defined environments; read names from the example file only
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** __tests__/, tests/, e2e/, *.test.*, *.spec.*
- **Read:** test file paths, test case titles and what they cover
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** the project's own build script (for example npm run build); it writes .next/ and prints the route table
- **Without running:** read the routes found above and say the list was read from the code, not run
