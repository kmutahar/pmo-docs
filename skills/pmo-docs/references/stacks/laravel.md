---
playbook_version: 1
---
Detected by: composer.json containing "laravel/framework", or artisan at repo root
Checked against: Laravel 13, Routing, Eloquent: Getting Started, Authentication, Authorization, Configuration, Testing: Getting Started, 2026-11-26
Unverified: Sanctum and Spatie permission package names, database/migrations column conventions

# Laravel

A full-stack PHP web application framework with Eloquent ORM, routing and Artisan CLI.

## Routes, pages or screens
- **Look in:** routes/web.php, routes/api.php, app/Http/Controllers/, resources/views/
- **Read:** Route::get/post/put/patch/delete/resource/apiResource, route groups and prefixes, controller actions, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** app/Models/, database/migrations/
- **Read:** Eloquent Model classes, $fillable/$casts, relations (hasMany, belongsTo, belongsToMany), migration schemas and enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** app/Policies/, app/Providers/, app/Http/Middleware/, routes/ (middleware calls)
- **Read:** Gate::define, Policy methods, auth/can middleware, authorize() calls, role and ability names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** config/*.php, .env.example, .env.sample, .env.template, env() calls in config/
- **Read:** config keys and environment variable names (APP_ENV); defined environments; read names from the example file only; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** tests/Feature/, tests/Unit/, tests/**/*Test.php (Pest, PHPUnit)
- **Read:** test functions and methods, HTTP request assertions ($this->get/post), covered routes and behaviors
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** php artisan route:list (needs the project's PHP environment, not a running server)
- **Without running:** read the routes found above and say the list was read from the code, not run
