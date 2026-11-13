---
playbook_version: 1
---
Detected by: pom.xml with spring-boot-starter or build.gradle with org.springframework.boot
Checked against: Spring Boot 4.1, Building a RESTful Web Service, Spring Data JPA, Spring Security Architecture, Externalized Configuration, Actuator endpoints, 2026-11-11
Unverified: springdoc /v3/api-docs, SPRING_PROFILES_ACTIVE, Flyway and Liquibase paths, test annotations other than @MockitoBean

# Spring Boot

An opinionated framework for building production-ready applications on the JVM.

## Routes, pages or screens
- **Look in:** src/main/java/**/*Controller.java, src/main/java/**/RouterConfig.java
- **Read:** @RestController, @RequestMapping, @GetMapping, @PostMapping, RouterFunction, path:line
- **Record as:** the endpoints or screens table of the document being drafted, each with path:line

## Data models
- **Look in:** src/main/java/**/model/, entity/, repository/, src/main/resources/db/migration/
- **Read:** @Entity classes, fields, @OneToMany/@ManyToOne relations, Flyway and Liquibase migrations
- **Record as:** data models table with entity names, field lists, relations and lifecycle states

## Permissions and auth
- **Look in:** SecurityConfig.java, SecurityFilterChain beans, method security annotations
- **Read:** @PreAuthorize, @Secured, hasRole/hasAuthority expressions, role names (with/without ROLE_)
- **Record as:** permissions entries as proposals (origin: proposed), roles compared with domain.roles

## Config and environments
- **Look in:** src/main/resources/application.properties, application.yaml or application.yml, application-*.yaml
- **Read:** property names, profile names (SPRING_PROFILES_ACTIVE); defined environments; key names only; stop reading a file if a value looks like a credential, and note it by file and line
- **Record as:** environments entries as proposals, variables as names

## Tests
- **Look in:** src/test/java/**/*Test.java (JUnit 5, MockMvc, WebTestClient, @MockitoBean)
- **Read:** @Test methods, @SpringBootTest, @WebMvcTest, endpoint assertions
- **Record as:** tests entries as proposals only when the user asks for them

## List the API live
- **Ask first:** Actuator /actuator/mappings (not exposed over HTTP by default; needs management.endpoints.web.exposure.include) or /v3/api-docs when springdoc is enabled; app must run
- **Without running:** read the routes found above and say the list was read from the code, not run
