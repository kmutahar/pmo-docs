---
playbook_version: 1
---
Detected by: *.csproj with Microsoft.AspNetCore.App or PackageReference to Microsoft.AspNetCore
Checked against: ASP.NET Core 10.0 (LTS), Overview of ASP.NET Core MVC, Minimal APIs overview, Authentication and authorization, Configuration in ASP.NET Core, 2026-11-11
Unverified: ASP.NET Core 11.0 (released 2026-11-10) changes, MapGroup, test project conventions

# ASP.NET Core

A cross-platform framework for building modern web applications and APIs with .NET.

## Routes, pages or screens
- **Look in:** Program.cs, Controllers/, Pages/ (*.cshtml), Components/ or Pages/ (*.razor)
- **Read:** [Route], [HttpGet/Post/Put/Delete], MapGet, MapPost, MapGroup, @page directives, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** Models/, Entities/, Data/, DbContext classes, Migrations/
- **Read:** entity classes, DbSet properties, relations, column types, enums and validation attributes
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** Program.cs (AddAuthorization, UseAuthentication, UseAuthorization), Controllers/, policies
- **Read:** [Authorize], [AllowAnonymous], policy names, Roles parameters, role names as in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** appsettings.json, appsettings.*.json, launchSettings.json
- **Read:** configuration keys and connection string names; ASPNETCORE_ENVIRONMENT profiles; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** test/, tests/, *Tests/*.cs (xUnit, NUnit, MSTest projects, WebApplicationFactory)
- **Read:** [Fact], [Theory], [Test] methods and tested endpoints
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** OpenAPI endpoint (/openapi/v1.json or /swagger/v1/swagger.json) when app is running
- **Without running:** read the routes found above and say the list was read from the code, not run
