---
playbook_version: 1
---
Detected by: pyproject.toml, requirements.txt or Pipfile containing "fastapi" or "flask"
Checked against: FastAPI 0.162 and Flask 3.1, First Steps, Bigger Applications, Security and OAuth2, Application Configuration, 2026-11-11
Unverified: the Security and OAuth2 page contents, flask routes, /openapi.json and /docs paths, Flask-Login and Flask-JWT-Extended names, test client calls

# FastAPI

A modern Python web framework for building APIs with type hints. Covers FastAPI and Flask.

## Routes, pages or screens
- **Look in:** main.py, app/api/, routers/, api/v1/ (APIRouter, include_router)
- **Read:** @app.get/post/put/delete, APIRouter decorators, path parameters, response_model, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line
- **Flask:** app.py, routes.py; @app.route, Blueprint, register_blueprint, view functions

## Data models
- **Look in:** models.py, schemas/, models/, schemas.py, database.py (SQLAlchemy, Pydantic, Alembic versions/)
- **Read:** Pydantic BaseModel schemas, SQLAlchemy declarative models, fields, types, relations and enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states
- **Flask:** models.py with Flask-SQLAlchemy (db.Model, Column, relationship), Flask-Marshmallow schemas

## Permissions and auth
- **Look in:** auth/, security.py, dependencies.py, core/security.py
- **Read:** Depends(...) with OAuth2PasswordBearer, Security scopes, current_user dependencies, role checks
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles
- **Flask:** Flask-Login (@login_required, current_user), Flask-JWT-Extended (@jwt_required), custom role decorators

## Config and environments
- **Look in:** core/config.py, config.py, .env.example, .env.sample, .env.template
- **Read:** pydantic-settings BaseSettings classes, os.getenv calls; defined environments; read names from the example file only
- **Record as:** environments entries as proposals, variables as names
- **Flask:** config.py, app.config.from_object/from_envvar, instance/config.py, from_prefixed_env, FLASK_DEBUG (FLASK_ENV was removed in Flask 2.3)

## Tests
- **Look in:** tests/, test_*.py, *_test.py (pytest, conftest.py, fixtures)
- **Read:** TestClient(app) calls, HTTP methods, tested paths, status assertions
- **Record as:** tests entries as proposals only when the user asks for them
- **Flask:** test_*.py using app.test_client(), client.get/post assertions

## List the API live
- **Ask first:** OpenAPI endpoint (/openapi.json or /docs) when the FastAPI app is running
- **Without running:** read the routes found above and say the list was read from the code, not run
- **Flask:** run flask routes to inspect registered URLs, only when the user approves running it
