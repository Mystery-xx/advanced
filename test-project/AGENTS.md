# TEST-PROJECT KNOWLEDGE BASE

**Generated:** 2026-07-28  
**Type:** Full-stack application (Spring Boot + React)

## OVERVIEW

Demo microservices application with 4 Spring Boot backends and React 18 frontend, orchestrated via Docker Compose.

## STRUCTURE

```
test-project/
├── backend/                 # 4 Spring Boot 2.7.18 services
│   ├── user-service/        # Port 8081, user management
│   ├── order-service/       # Port 8082, order processing
│   ├── payment-service/     # Port 8083, payment handling
│   └── weather-mcp-service/ # Port 8084, weather API + MCP
├── frontend/                # React 18 + TS + Vite (port 3000)
├── journeys/                # Gherkin BDD features (3 .feature files)
└── docker-compose.yaml      # Postgres 15 + backend:8080 + frontend:3000
```

## WHERE TO LOOK

| Need | Location |
|------|----------|
| User management | `backend/user-service/src/main/java/com/example/userservice/` |
| Order processing | `backend/order-service/src/main/java/com/example/orderservice/` |
| Payment logic | `backend/payment-service/src/main/java/com/example/paymentservice/` |
| API | `backend/weather-mcp-service/src/main/java/com/example/weathermcpservice/` |
| React pages | `frontend/src/pages/` (6 pages) |
| API client | `frontend/src/api/` (axios-based) |
| Auth context | `frontend/src/context/AuthContext.tsx` |
| BDD features | `journeys/*.feature` |

## CODE MAP

| Backend Service | Application Class | Controller | Repository |
|-----------------|-------------------|------------|------------|
| user-service | `UserServiceApplication.java` | `UserController.java` | `UserRepository.java` |
| order-service | `OrderServiceApplication.java` | `OrderController.java` | `OrderRepository.java` |
| payment-service | `PaymentServiceApplication.java` | `PaymentController.java` | `PaymentRepository.java` |
| weather-mcp-service | `WeatherMcpServiceApplication.java` | `WeatherController.java` | N/A (external API) |

| Frontend | File |
|----------|------|
| Entry point | `src/main.tsx` |
| App router | `src/App.tsx` |
| Auth context | `src/context/AuthContext.tsx` |
| API client | `src/api/client.ts` |

## CONVENTIONS

- **Spring Boot layering:** controller → service → repository → entity
- **DTOs:** Separate `dto/` package for request/response objects
- **Config:** `application.properties` per service
- **Frontend:** Functional components with hooks, TypeScript interfaces
- **Routing:** React Router v6 with protected routes

## ANTI-PATTERNS (THIS SUBTREE)

- ⚠️ Spring Boot 2.7.18 (Java 11) vs root POM 3.4.1 (Java 17) - conflict
- ⚠️ `jour/steps/` - BDD features have no step definitions
- ⚠️ JaCoCo/Allure only in user-service and order-service (inconsistent test coverage)
- ⚠️ Dockerfile only deploys user-service JAR (ignores other 3 services)

## UNIQUE STYLES

- Each backend service is independent Maven module with own POM
- Weather service integrates external API + MCP protocol
- Frontend uses axios interceptors for auth token injection
- BDD features written but steps not implemented (pending)

## COMMANDS

```bash
# Run individual backend service
cd backend/user-service && mvn spring-boot:run

# Run frontend
cd frontend && npm run dev

# Run all services + Postgres
docker-compose up

# Run BDD tests (steps not implemented yet)
# journeys/ contains .feature files but steps/ is empty
```

## NOTES

- Backend services communicate via REST (no event bus)
- Postgres 15 shared database (configured in docker-compose.yaml)
- Frontend has 6 pages: Home, Login, Signup, Dashboard, Orders, Weather
- Auth flow: JWT tokens stored in localStorage, injected via axios interceptor
- MCP (Model Context Protocol) integration in weather service