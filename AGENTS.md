# PROJECT KNOWLEDGE BASE

**Generated:** 2026-07-28  
**Type:** Full-stack demo application

## OVERVIEW

Spring Boot 3.x microservices backend + React 18/TypeScript/Vite frontend with Docker Compose orchestration and Playwright E2E testing.

## STRUCTURE

```
.
├── test-project/              # Main application
│   ├── backend/               # 4 Spring Boot 2.7.18 microservices
│   ├── frontend/              # React 18 + TS + Vite
│   └── journeys/              # BDD feature files (empty steps)
├── .opencode/                 # Agent configuration (CP servers
├── .github/workflows/         # CI pipeline
├── rules/                     # ⚠️ MISMATCHED AGENTS.md files
└── run-ui-tests.js            # Playwright E2E runner
```

## WHERE TO LOOK

| Need | Location |
|------|----------|
| Backend services | `test-project/backend/{user,order,payment,weather-mcp}-service/` |
| Frontend pages | `test-project/frontend/src/pages/` |
| Agent config | `.opencode/mcp.json`, `.opencode/agents/` |
| E2E tests | `journeys/*.feature`, `run-ui-tests.js` |
| Docker setup | `test-project/docker-compose.yaml` |

## CODE MAP

| Component | Entry Point | Port |
|-----------|-------------|------|
| user-service | `UserServiceApplication.java` | 8081 |
| order-service | `OrderServiceApplication.java` | 8082 |
| payment-service | `PaymentServiceApplication.java` | 8083 |
| weather-mcp-service | `WeatherMcpServiceApplication.java` | 8084 |
| frontend | `frontend/src/main.tsx` | 3000 |

## CONVENTIONS

- **Backend:** Spring Boot 2.7.18 (⚠️ root POM says 3.4.1 - mismatch)
- **Frontend:** React 18 + Vite + TypeScript
- **Test structure:** `src/test/java/` for unit, `journeys/` for BDD
- **ocker:** Postgres 15 + services on 8081-8084

## ANTI-PATTERNS (THIS PROJECT)

- ⚠️ `rules/AGENTSv1.md` and `rules/AGENTSv2.md` describe DIFFERENT PROJECT (Leroy Merlin Kotlin/Cucumber)
- ⚠️ `.opencode/system-prompt.md` describes DIFFERENT PROJECT
- ⚠️ Spring Boot version mismatch: root POM 3.4.1 vs backend POM 2.7.18
- ⚠️ `.codegraph/` directory EMPTY - codegraph_explore won't work
- ⚠️ `journeys/steps/` directory EMPTY - BDD features cannot execute
- ⚠️ CI expects `journeys/playwright-test` but runner is at root `run-ui-tests.js`
- ⚠️ Dockerfile builds 4 modules but only deploys user-service JAR
- ⚠️ JaCoCo/Allure only in user-service and order-service (inconsistent)
- ⚠️ No linters configured (missing .eslintrc, .prettierrc, .editorconfig)

## UNIQUE STYLES

- Multi-module backend with separate POMs per service
- BDD feature files without step definitions (pending implementation)
- Playwright runner as standalone JS (not Maven/Gradle integrated)

## COMMANDS

```bash
# Backend (each service)
cd test-project/backend/user-service && mvn spring-boot:run

# Frontend
cd test-project/frontend && npm run dev

# E2E tests
node run-ui-tests.js

# Docker (all services + Postgres)
cd test-project && docker-compose up
```

## NOTES

- Backend services use Java 11 (despite root POM claiming Java 17)
- Frontend uses axios for API calls, React v6 for navigation
- Auth context (`useAuth`) present in
- 6 frontend pages: Home, Login, Signup, Dashboard, Orders, Weather
- MCP servers configured: Playwright, CodeGraph, AST-Index (not indexed)