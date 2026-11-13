---
playbook_version: 1
---
Detected by: manage.py, or requirements.txt / pyproject.toml containing "django" or "Django"
Checked against: Django 6.1, URL dispatcher, Writing views, Models and migrations, User authentication, Django settings, 2026-11-11
Unverified: DATABASES keys, client.get in tests, the Models and migrations page, DRF permission names

# Django

A high-level Python web framework with ORM, authentication and admin.

## Routes, pages or screens
- **Look in:** **/urls.py, **/views.py, api/urls.py, views/ (Django and Django REST framework)
- **Read:** path(), re_path(), include(), ViewSet routers, View classes and view functions, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** **/models.py, models/, **/migrations/*.py
- **Read:** models.Model classes, Field types, ForeignKey/ManyToManyField relations, choices enums
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** views.py, api/permissions.py, settings.py (AUTHENTICATION_BACKENDS)
- **Read:** @login_required, @permission_required, DRF permission_classes, Group and Permission checks
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** settings.py, settings/*.py, .env.example, .env.sample, .env.template, DJANGO_SETTINGS_MODULE references
- **Read:** setting names (ALLOWED_HOSTS, DATABASES keys); defined environments; read names from the example file only
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** **/tests.py, tests/, test_*.py (TestCase, SimpleTestCase, APITestCase, pytest-django)
- **Read:** test methods, client.get/post endpoint assertions
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** drf-spectacular's manage.py spectacular command (DRF's built-in generateschema is deprecated); needs the project's Python environment, not a running server
- **Without running:** read the routes found above and say the list was read from the code, not run
