---
playbook_version: 1
---
Detected by: package.json dependencies containing "nuxt", or nuxt.config.{ts,js,mjs}
Checked against: Nuxt 4.7, Nuxt Directory Structure, Routing, server, Configuration, Testing, 2026-11-26
Unverified: NUXT_PUBLIC_ env prefix convention, auth module names (nuxt-auth-utils, sidebase), Prisma and Drizzle locations

# Nuxt

A full-stack Vue framework with file-based routing and Nitro server API routes.

## Routes, pages or screens
- **Look in:** app/pages/ or pages/, server/api/, server/routes/
- **Read:** page files and dynamic segments ([id], [...slug]), defineEventHandler handlers, HTTP method suffixes (.get, .post), path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** shared/types/, types/, server/database/, prisma/schema.prisma, drizzle/
- **Read:** TypeScript interfaces/types, ORM schemas and models, fields, relations and lifecycle states
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** app/middleware/ or middleware/, server/middleware/, server/utils/, definePageMeta middleware references
- **Read:** route middleware guards, server session/token checks, role checks and role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** nuxt.config.{ts,js,mjs}, .env.example, .env.sample, .env.template
- **Read:** runtimeConfig keys (public vs private), environment variable names; defined environments; read names from the example file only; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** test/, tests/, **/*.spec.ts, **/*.test.ts (@nuxt/test-utils, Vitest)
- **Read:** describe/it blocks, mountSuspended and $fetch assertions, covered pages and API routes
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** project OpenAPI endpoint if enabled in Nitro/Nuxt, or inspect built routes after running the project's build script
- **Without running:** read the routes found above and say the list was read from the code, not run
