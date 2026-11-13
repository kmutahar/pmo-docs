---
playbook_version: 1
---
Detected by: package.json dependencies containing "express"
Checked against: Express 5, Routing, Router, Using Middleware, 2026-11-11
Unverified: Passport and JWT names, test tools, NODE_ENV, Express 5 path syntax changes (for example wildcards need a name)

# Express

A minimalist web framework for Node.js routing and middleware.

## Routes, pages or screens
- **Look in:** app.js, server.js, index.js, src/index.*, routes/, src/routes/, controllers/
- **Read:** app.METHOD, app.use with Router, router.METHOD, mount paths, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** models/, schemas/, prisma/schema.prisma, entities/ (Mongoose, Sequelize, Prisma, TypeORM)
- **Read:** entity names, schema fields, associations, model validations, states and enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** middleware/, auth/, passport strategies, JWT verification, role guard functions
- **Read:** middleware chain order, req.user checks, role checks, role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** config/, .env.example, .env.sample, .env.template, process.env references, dotenv loading
- **Read:** environment variable names and config keys; defined environments (NODE_ENV); read names from the example file only
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** test/, tests/, __tests__/, *.test.js, *.spec.js (Mocha, Jest, Supertest)
- **Read:** describe and it blocks, endpoint assertions, what endpoints are covered
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** project OpenAPI specification or swagger endpoint if present; requires app running
- **Without running:** read the routes found above and say the list was read from the code, not run
