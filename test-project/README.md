# Test Project - Full-Stack Microservices Demo

[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-2.7.18-green.svg)](https://spring.io/projects/spring-boot)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)

A demo microservices application showcasing Spring Boot backend services with React frontend, orchestrated via Docker Compose.

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          REACT FRONTEND                             │
│                         http://localhost:3000                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   Home   │ │  Login   │ │  Signup  │ │Dashboard │ │ Orders   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐                                                      │
│  │ Weather  │                                                      │
│  └──────────┘                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ axios HTTP client
                              │ JWT Authentication
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DOCKER NETWORK (bridge)                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  API Gateway / Load Balancer                                 │  │
│  │  http://backend:8080                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                │
│         │                    │                    │                │
│         ▼                    ▼                    ▼                │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│  │user-service │     │order-service│     │payment-svc  │          │
│  │  :8081      │     │  :8082      │     │  :8084      │          │
│  │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │          │
│  │ │Controller│ │     │ │Controller│ │    │ │Controller│ │         │
│  │ │Service  │ │     │ │Service  │ │     │ │Service  │ │          │
│  │ │Repository│ │     │ │Repository│ │    │ │Repository│ │         │
│  │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │          │
│  └─────────────┘     └─────────────┘     └─────────────┘          │
│         │                    │                    │                │
│         └────────────────────┼────────────────────┘                │
│                              │                                     │
│                              ▼                                     │
│                     ┌─────────────┐                                │
│                     │weather-mcp  │                                │
│                     │  :8083      │                                │
│                     │ ┌─────────┐ │                                │
│                     │ │Controller│ │                               │
│                     │ │MCP Impl │ │                                │
│                     │ └─────────┘ │                                │
│                     └─────────────┘                                │
│                              │                                     │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
                               ▼
                     ┌─────────────────┐
                     │  PostgreSQL 15  │
                     │  :5432/testdb   │
                     │                 │
                     │ ┌─────────────┐ │
                     │ │  Users      │ │
                     │ │  Orders     │ │
                     │ │  Payments   │ │
                     │ │  Roles      │ │
                     │ └─────────────┘ │
                     └─────────────────┘
```

## 📊 Port Mapping Table

| Service | Container Port | Host Port | Protocol | Purpose |
|---------|---------------|-----------|----------|---------|
| **frontend** | 80 | 3000 | HTTP | React SPA (Nginx in production) |
| **backend-gateway** | 8080 | 8080 | HTTP | Unified API entry point |
| **user-service** | 8081 | 8081 | HTTP | User management & authentication |
| **order-service** | 8082 | 8082 | HTTP | Order processing |
| **weather-mcp-service** | 8083 | 8083 | HTTP | Weather API + MCP |
| **payment-service** | 8084 | 8084 | HTTP | Payment processing |
| **postgresql** | 5432 | 5432 | TCP | Database |

### Service Details

| Service | Technology | Database | Swagger UI |
|---------|------------|----------|------------|
| user-service | Spring Boot 2.7.18 | PostgreSQL | http://localhost:8081/swagger-ui.html |
| order-service | Spring Boot 2.7.18 | PostgreSQL | http://localhost:8082/swagger-ui.html |
| weather-mcp-service | Spring Boot 2.7.18 | H2 (dev) | http://localhost:8083/swagger-ui.html |
| payment-service | Spring Boot 2.7.18 | PostgreSQL | http://localhost:8084/swagger-ui.html |

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- (Optional) Node.js 18+ for frontend development
- (Optional) Java 11+ and Maven 3.6+ for backend development

### Running with Docker Compose

```bash
# Navigate to test-project directory
cd test-project

# Start all services (PostgreSQL + Backend + Frontend)
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend Gateway: http://localhost:8080
# Swagger UI: http://localhost:8080/swagger-ui.html
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove data volumes
docker-compose down -v
```

## ⏱️ Service Startup Sequence

### Automatic (Docker Compose)

```
1. PostgreSQL Container
   ├─ Image: postgres:15
   ├─ Port: 5432
   └─ Health Check: pg_isready -U testuser -d testdb (every 5s)
   
   ↓ (waits for: condition: service_healthy)
   
2. Backend Container
   ├─ Build: ./backend/Dockerfile
   ├─ Port: 8080
   ├─ Environment: SPRING_PROFILES_ACTIVE=docker
   └─ Health Check: curl -f http://localhost:8080/actuator/health (every 10s)
   
   ↓ (waits for: depends_on - backend)
   
3. Frontend Container
   ├─ Build: ./frontend/Dockerfile
   ├─ Port: 3000:80
   └─ Environment: VITE_API_URL=http://backend:8080

✅ Application Ready
   ├─ Frontend: http://localhost:3000
   ├─ API Gateway: http://localhost:8080
   └─ Database: localhost:5432
```

### Manual Startup

```bash
# Step 1: Start PostgreSQL
docker-compose up -d postgres
sleep 10  # Wait for database initialization

# Step 2: Build backend services
cd backend
mvn clean package -DskipTests

# Step 3: Start backend services (each in separate terminal)
cd user-service && mvn spring-boot:run
cd order-service && mvn spring-boot:run
cd weather-mcp-service && mvn spring-boot:run
cd payment-service && mvn spring-boot:run

# Step 4: Start frontend
cd frontend
npm install
npm run dev

# Step 5: Verify all services
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
curl http://localhost:8083/actuator/health
curl http://localhost:8084/actuator/health
```

## 🔧 Environment Variables

### Docker Compose Configuration

```yaml
# PostgreSQL Service
environment:
  POSTGRES_DB: testdb
  POSTGRES_USER: testuser
  POSTGRES_PASSWORD: testpass

# Backend Service
environment:
  SPRING_PROFILES_ACTIVE: docker
  SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/testdb
  SPRING_DATASOURCE_USERNAME: testuser
  SPRING_DATASOURCE_PASSWORD: testpass

# Frontend Service
environment:
  VITE_API_URL: http://backend:8080
```

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPRING_PROFILES_ACTIVE` | Yes | `dev` | Spring profile (`dev`, `docker`, `prod`) |
| `SPRING_DATASOURCE_URL` | Yes | - | JDBC connection URL |
| `SPRING_DATASOURCE_USERNAME` | Yes | - | Database username |
| `SPRING_DATASOURCE_PASSWORD` | Yes | - | Database password |
| `SERVER_PORT` | No | 808x | HTTP server port |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | `http://localhost:8080` | Backend API base URL |
| `VITE_API_TIMEOUT` | No | `30000` | API request timeout (ms) |

### Local Development Setup

```bash
# Backend (application.properties)
cd backend/user-service/src/main/resources
# Edit application.properties with your database credentials

# Frontend (.env)
cd frontend
cat > .env << EOF
VITE_API_URL=http://localhost:8080
VITE_API_TIMEOUT=30000
EOF
```

## 🏃 Running Individual Services

### Backend Services

```bash
# Build all backend services
cd backend
mvn clean install

# Run user-service (port 8081)
cd user-service
mvn spring-boot:run

# Run order-service (port 8082)
cd order-service
mvn spring-boot:run

# Run weather-mcp-service (port 8083)
cd weather-mcp-service
mvn spring-boot:run

# Run payment-service (port 8084)
cd payment-service
mvn spring-boot:run
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🧪 Testing

### Backend Unit Tests

```bash
# Run all tests
cd backend && mvn test

# Run tests with coverage (user-service, order-service)
cd user-service && mvn test jacoco:report allure:serve

# Skip tests during build
mvn package -DskipTests
```

### E2E Tests (Playwright)

```bash
# From project root
cd /mnt/f/git/advanced
node run-ui-tests.js

# BDD feature files
# Location: test-project/journeys/
# Note: Step definitions not implemented yet
```

### API Testing Examples

```bash
# Health endpoints
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
curl http://localhost:8083/actuator/health
curl http://localhost:8084/actuator/health

# User endpoints
curl http://localhost:8081/api/users
curl -X POST http://localhost:8081/api/users \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"secret"}'

# Order endpoints
curl http://localhost:8082/api/orders
curl http://localhost:8082/api/orders/1

# Weather endpoints
curl http://localhost:8083/api/weather/city/London

# Payment endpoints
curl http://localhost:8084/api/payments
curl http://localhost:8084/api/payments/1
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use

**Problem:** One or more ports (3000, 5432, 8080-8084) are already in use.

**Solution:**
```bash
# Find process using the port
lsof -i :8081
lsof -i :3000
lsof -i :5432

# Kill the process
kill -9 <PID>

# Or change port in configuration files
```

#### 2. Database Connection Failed

**Problem:** Backend cannot connect to PostgreSQL.

**Solution:**
```bash
# Check PostgreSQL container status
docker ps | grep postgres

# View PostgreSQL logs
docker logs test-project-postgres

# Test database connection
docker exec -it test-project-postgres psql -U testuser -d testdb

# Verify network connectivity
docker exec -it test-project-backend ping postgres
```

#### 3. Backend Service Won't Start

**Problem:** Spring Boot application fails to start.

**Solution:**
```bash
# Check Java version (requires Java 11+)
java -version

# Check Maven version
mvn -version

# Clean and rebuild
cd backend
mvn clean install

# View backend logs
docker logs test-project-backend --tail 100

# Check database is accessible
docker exec -it test-project-backend \
  curl http://postgres:5432  # Should fail, but tests connectivity
```

#### 4. Frontend Cannot Connect to Backend

**Problem:** React app shows network errors.

**Solution:**
```bash
# Check environment variable
cat frontend/.env

# Verify backend is accessible
curl http://localhost:8080/actuator/health

# Check CORS configuration in backend
# Backend must allow frontend origin (http://localhost:3000)

# Test from inside frontend container
docker exec -it test-project-frontend \
  curl http://backend:8080/actuator/health
```

#### 5. Docker Compose Issues

**Problem:** Services fail to start or communicate.

**Solution:**
```bash
# Stop and clean everything
docker-compose down -v
docker-compose down --remove-orphans

# Remove dangling images
docker image prune -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up

# Check Docker resources
docker system df
docker stats
```

#### 6. Service Health Check Fails

**Problem:** Docker reports unhealthy containers.

**Solution:**
```bash
# View service logs
docker logs test-project-backend --tail 100

# Manually test health endpoint
docker exec -it test-project-backend \
  curl http://localhost:8080/actuator/health

# Increase health check timeouts in docker-compose.yaml
# healthcheck:
#   interval: 30s
#   timeout: 10s
#   retries: 10
#   start_period: 40s
```

#### 7. Frontend Build Errors

**Problem:** npm build or dev fails.

**Solution:**
```bash
cd frontend

# Clear dependencies and cache
rm -rf node_modules package-lock.json
rm -rf node_modules/.vite

# Reinstall dependencies
npm install

# Check TypeScript errors
npx tsc --noEmit

# Check for outdated packages
npm outdated

# Fix security vulnerabilities
npm audit fix
```

### Log Access

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker logs test-project-backend --tail 100

# Backend Maven logs
ls backend/*/target/*.log

# Real-time monitoring
watch -n 1 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

### Performance Issues

```bash
# Monitor container resource usage
docker stats

# Check PostgreSQL performance
docker exec -it test-project-postgres \
  psql -U testuser -d testdb -c "SELECT * FROM pg_stat_activity;"

# Enable slow query logging in PostgreSQL
# Add to postgresql.conf:
# log_min_duration_statement = 1000

# Check backend memory usage
docker exec -it test-project-backend \
  ps aux | grep java
```

### Network Debugging

```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect test-project_default

# Test inter-container connectivity
docker exec -it test-project-backend \
  nc -zv postgres 5432

# Check DNS resolution
docker exec -it test-project-backend \
  getent hosts postgres
```

## 📁 Project Structure

```
test-project/
├── README.md                    # This file
├── docker-compose.yaml          # Docker orchestration
│
├── backend/                     # Spring Boot microservices
│   ├── pom.xml                  # Parent POM (Spring Boot 2.7.18)
│   ├── user-service/            # Port 8081 - User management
│   │   ├── pom.xml              # JaCoCo + Allure configured
│   │   └── src/main/java/...
│   ├── order-service/           # Port 8082 - Order processing
│   │   ├── pom.xml              # JaCoCo + Allure configured
│   │   └── src/main/java/...
│   ├── weather-mcp-service/     # Port 8083 - Weather API + MCP
│   │   ├── pom.xml
│   │   └── src/main/java/...
│   └── payment-service/         # Port 8084 - Payment processing
│       ├── pom.xml
│       └── src/main/java/...
│
├── frontend/                    # React 18 + TypeScript + Vite
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx             # Entry point
│       ├── App.tsx              # Root component + router
│       ├── pages/               # 6 page components
│       ├── components/          # Reusable components
│       ├── context/             # AuthContext
│       ├── api/                 # API client (axios)
│       └── hooks/               # Custom hooks
│
└── journeys/                    # BDD feature files
    ├── login.feature
    ├── order.feature
    ├── weather.feature
    └── steps/                   # (Empty - pending implementation)
```

## 🔗 Service Communication

### Inter-Service Calls

```
Frontend → Gateway (8080) → Backend Services (8081-8084)
                                      ↓
                              PostgreSQL (5432)
```

### API Endpoints Summary

| Service | Base URL | Key Endpoints |
|---------|----------|---------------|
| user-service | `/api/users` | `POST /register`, `POST /login`, `GET /{id}` |
| order-service | `/api/orders` | `GET /`, `POST /`, `GET /{id}` |
| payment-service | `/api/payments` | `GET /`, `POST /`, `GET /{id}` |
| weather-mcp-service | `/api/weather` | `GET /city/{name}`, `GET /forecast` |

## 📝 Known Issues

### Version Mismatches

- ⚠️ Root POM claims Spring Boot 3.4.1, but backend services use 2.7.18
- ⚠️ Root POM claims Java 17, but backend services use Java 11
- ⚠️ JaCoCo/Allure only configured in user-service and order-service

### Docker Limitations

- ⚠️ Dockerfile only deploys user-service JAR (ignores other 3 services)
- ⚠️ No service discovery or load balancing configured

### Testing Gaps

- ⚠️ BDD feature files exist but step definitions are not implemented
- ⚠️ No E2E test integration with Docker Compose

## 📚 Additional Resources

- [Root Project README](../README.md)
- [Backend Services Documentation](./backend/README.md)
- [Frontend Documentation](./frontend/README.md)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

**Last Updated:** 2026-07-28  
**Version:** 1.0.0  
**Maintainer:** Test Project Team