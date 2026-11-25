---
playbook_version: 1
---
Detected by: Gemfile containing "rails", or config/routes.rb with bin/rails
Checked against: Ruby on Rails 8.1, Rails Routing from the Outside In, Active Record Basics, Active Record Associations, Configuring Rails Applications, Testing Rails Applications, Securing Rails Applications, 2026-11-26
Unverified: Devise, Pundit, CanCanCan and RSpec names, Active Record enum syntax

# Ruby on Rails

A convention-over-configuration Ruby web framework with Active Record and MVC structure.

## Routes, pages or screens
- **Look in:** config/routes.rb, app/controllers/**/*_controller.rb, app/views/
- **Read:** resources/resource, namespace/scope, get/post/patch/put/delete routes, controller actions, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** app/models/, db/schema.rb, db/migrate/
- **Read:** ApplicationRecord models, belongs_to/has_many/has_one associations, validations, enums and schema columns
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** app/controllers/concerns/, app/policies/, app/models/ability.rb, before_action callbacks
- **Read:** authentication concerns, Devise/Pundit/CanCanCan hooks, before_action guards, role names as spelled in code
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** config/application.rb, config/environments/*.rb, config/database.yml, .env.example, .env.sample, .env.template
- **Read:** RAILS_ENV environment files, ENV keys, config settings; read names from the example file only; never open config/master.key or decrypt credentials; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** test/**/*_test.rb (Minitest: ActiveSupport::TestCase, ActionDispatch::IntegrationTest), spec/**/*_spec.rb (RSpec)
- **Read:** test blocks, request/integration assertions, covered endpoints and behaviors
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** bin/rails routes (needs the project's Ruby environment, not a running server)
- **Without running:** read the routes found above and say the list was read from the code, not run
