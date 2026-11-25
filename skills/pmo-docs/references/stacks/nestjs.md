---
playbook_version: 1
---
Detected by: package.json dependencies containing "@nestjs/core", or nest-cli.json
Checked against: NestJS 12, Controllers, Guards, OpenAPI (Swagger), 2026-11-26
Unverified: ConfigModule/ConfigService setup, TypeORM/Prisma/Mongoose locations, Test.createTestingModule and Supertest conventions

# NestJS

A progressive TypeScript framework for building structured Node.js server-side applications.

## Routes, pages or screens
- **Look in:** src/**/*.controller.ts, src/**/*.module.ts, src/main.ts (global prefix, versioning)
- **Read:** @Controller, @Get/@Post/@Put/@Patch/@Delete decorators, route parameters, DTO classes, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** src/**/*.entity.ts, src/**/*.schema.ts, src/**/dto/*.ts, prisma/schema.prisma
- **Read:** entity/schema classes, DTO fields, relations, enums and validation decorators
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** src/**/*.guard.ts, src/**/auth/, custom metadata decorators (@SetMetadata)
- **Read:** CanActivate guards, @UseGuards, Reflector metadata checks, role decorators and role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** src/**/config/, .env.example, .env.sample, .env.template, ConfigModule/ConfigService and process.env references
- **Read:** config keys and environment variable names (NODE_ENV); defined environments; read names from the example file only; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** src/**/*.spec.ts, test/**/*.e2e-spec.ts (Jest, Supertest)
- **Read:** Test.createTestingModule setups, describe/it blocks, HTTP endpoint assertions
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** OpenAPI endpoint (/api-json or Swagger UI at /api via SwaggerModule) when the app is running
- **Without running:** read the routes found above and say the list was read from the code, not run
