# BACKEND KNOWLEDGE BASE

**Generated:** 2026-07-28  
**Type:** Spring Boot 2.7.18 multi-module microservices

## OVERVIEW

4 independent Spring Boot microservices with Maven multi-module structure. Each service has its own POM, ports 8081-8084.

## STRUCTURE

```
backend/
├── pom.xml                  # Parent POM (Spring Boot 2.7.18, Java 11)
├── user-service/            # Port 8081, user management + auth
│   ├── src/main/java/com/example/userservice/
│   │   ├── controller/      # REST endpoints
│   │   ├── service/         # Business logic
│   │   ├── repository/      # JPA repositories
│   │   ├── entity/          # JPA entities
│   │   ├── dto/             # Request/response DTOs
│   │   └── config/          # Security, CORS, Swagger
│   └── pom.xml              # JaCoCo + Allure configured
├── order-service/           # Port 8082, order processing
│   └── pom.xml              # JaCoCo + Allure configured
├── payment-service/         # Port 8083, payment handling
│   └── pom.xml              # No JaCoCo/Allure
└── weather-mcp-service/     # Port 8084, weather API + MCP
    └── pom.xml              # No JaCoCo/Allure
```

## WHERE TO LOOK

| Concern | Location Pattern |
|---------|------------------
| REST controllers | `{service}/src/main/java/com/example/{service}/controller/`
| Business logic | `{service}/.../service/` |
| Database access | `{service}/.../repository/` |
| JPA entities | `{service}/.../entity/` |
| DTOs | `{service}/.../dto/` |
| Security config | `{service}/.../config/SecurityConfig.java` |
| Application props | `{service}/src/main/resources/application.properties` |

## CODE MAP

| Service | Main Class | Key Entities | Port |
|---------|------------|--------------|------|
| user-service | `UserServiceApplication` | `User`, `Role` | 8081 |
| order-service | `OrderServiceApplication` | `Order`, `OrderItem` | 8082 |
| payment-service | `PaymentServiceApplication` | `Payment`, `Transaction` | 8083 |
| weather-mcp-service | `WeatherMcpServiceApplication` | N/A (stateless) | 8084 |

## CONVENTIONS

- **Layering:** controller → service → repository → entity
- **Naming:** `{Entity}Controller`, `{Entity}Service`, `{Entity}Repository`
- **DTOs:** `{Entity}Request`, `{Entity}Response`, `{Entity}Mapper`
- **Exception handling:** `@ControllerAdvice` with custom `ErrorResponse`
- **Validation:** JSR-303 (`@Valid`, `@NotNull`, `@Size`)
- **API docs:** Swagger/OpenAPI via `springdoc-openapi`

## ANTI-PATTERNS (BACKEND)

- ⚠️ Spring Boot 2.7.18 (Java 11) conflicts with root POM 3.4.1 (Java 17)
- ⚠️ JaCoCo/Allure only in user-service and order-service (inconsistent)
- ⚠️ payment-service and weather-mcp-service lack test coverage tools
- ⚠️ No shared common module (code duplication across services)
- ⚠️ Dockerfile only deploys user-service (ignores other 3 services)

## UNIQUE STYLES

- Each service is fully independent (no shared JAR)
- Weather service implements MCP (Model Context Protocol)
- User service handles JWT auth for all services
- Order service calls payment service via REST (synchronous)

## COMMANDS

```bash
# Build all services
mvn clean install

# Run specific service
cd user-service && mvn spring-boot:run

# Run tests with coverage (user-service, order-service only)
cd user-service && mvn test jacoco:report allure:serve

# Generate JARs
mvn package
```

## NOTES

- **Java version:** 11 (despite root POM claiming 17)
- **Database:** Postgres 15 (configured in docker-compose.yaml)
- **Inter-service communication:** REST (no event bus)
- **Security:** JWT tokens, stateless authentication
- **Missing:** No circuit breaker, no service discovery, no centralized logging