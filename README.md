# Advanced Microservices Project

[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-2.7.18-green.svg)](https://spring.io/projects/spring-boot)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

A full-stack microservices demo application with Spring Boot backend services and React frontend, orchestrated with Docker Compose.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Service Port Mapping](#service-port-mapping)
- [Quick Start](#quick-start)
- [Docker Compose Setup](#docker-compose-setup)
- [Service Startup Sequence](#service-startup-sequence)
- [Environment Variables](#environment-variables)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React 18)                     │
│                         Port: 3000                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   HomePage  │  │  LoginPage  │  │ SignupPage  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Dashboard   │  │ OrdersPage  │  │ WeatherPage │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST (axios)
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY / LOAD BALANCER                  │
│                         Port: 8080                              │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  user-service    │ │  order-service   │ │ payment-service  │
│  Port: 8081      │ │  Port: 8082      │ │  Port: 8084      │
│  ┌────────────┐  │ │  ┌────────────┐  │ │  ┌────────────┐  │
│  │ UserController│ │ │  │ OrderController│ ││ PaymentCtrl│  │
│  │ UserService │  │ │  │ OrderService│  │ │ PaymentSvc │  │
│  │ UserRepository││ │  │ OrderRepo │  │ │ PaymentRepo│  │
│  └────────────┘  │ │  └────────────┘  │ │  └────────────┘  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │ weather-mcp-svc  │
                    │ Port: 8083       │
                    │ WeatherController│
                    │ MCP Integration  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   PostgreSQL 15  │
                    │   Port: 5432     │
                    │   Database:      │
                    │   - testdb       │
                    │   - User         │
                    │   - Orders       │
                    │   - Payments     │
                    └──────────────────┘
```

## 🗺️ Service Port Mapping

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| **frontend** | 3000 | HTTP | React 18 SPA (Vite dev server) |
| **backend-gateway** | 8080 | HTTP | Unified API gateway (Docker) |
| **user-service** | 8081 | HTTP | User management, authentication, JWT |
| **order-service** | 8082 | HTTP | Order processing, order items |
| **weather-mcp-service** | 8083 | HTTP | Weather API, MCP integration |
| **payment-service** | 8084 | HTTP | Payment processing, transactions |
| **postgresql** | 5432 | TCP | Database (Postgres 15) |

### Internal Service Communication

```
Frontend (3000) → Gateway (8080) → Backend Services (8081-8084)
                                             ↓
                                    PostgreSQL (5432)
```

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Node.js** 18+ and **npm** (for local frontend development)
- **Java** 11+ and **Maven** 3.6+ (for local backend development)

### Option 1: Docker Compose (Recommended)

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

### Option 2: Local Development

```bash
# 1. Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=testdb \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -p 5432:5432 \
  postgres:15

# 2. Start backend services (in separate terminals)
cd test-project/backend/user-service && mvn spring-boot:run
cd test-project/backend/order-service && mvn spring-boot:run
cd test-project/backend/payment-service && mvn spring-boot:run
cd test-project/backend/weather-mcp-service && mvn spring-boot:run

# 3. Start frontend
cd test-project/frontend && npm install && npm run dev
```

## 🐳 Docker Compose Setup

### Configuration File

Located at: `test-project/docker-compose.yaml`

### Services Defined

```yaml
version: '3.8'

services:
  postgres:      # PostgreSQL 15 database
  backend:       # Spring Boot backend (port 8080)
  frontend:      # React frontend (port 3000)
```

### Commands

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Build and start
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Scale services (if stateless)
docker-compose up --scale backend=2
```

### Health Checks

- **PostgreSQL**: `pg_isready -U testuser -d testdb` (every 5s)
- **Backend**: `curl -f http://localhost:8080/actuator/health` (every 10s)
- **Frontend**: Depends on backend health

## ⏱️ Service Startup Sequence

### Docker Compose (Automatic)

```
1. PostgreSQL starts
   ↓ (healthcheck: pg_isready)
2. Backend starts
   ↓ (depends_on: postgres healthy)
   ↓ (healthcheck: /actuator/health)
3. Frontend starts
   ↓ (depends_on: backend)
4. Application ready at http://localhost:3000
```

### Manual Startup (Step by Step)

```bash
# Step 1: Start PostgreSQL (wait 10 seconds)
docker-compose up -d postgres
sleep 10

# Step 2: Start backend services
cd test-project/backend
mvn clean install  # Build all services

# Start each service (in separate terminals or background)
cd user-service && mvn spring-boot:run &
cd order-service && mvn spring-boot:run &
cd payment-service && mvn spring-boot:run &
cd weather-mcp-service && mvn spring-boot:run &

# Wait for services to be ready (check logs)
sleep 15

# Step 3: Start frontend
cd test-project/frontend
npm install
npm run dev

# Step 4: Verify all services
curl http://localhost:8081/actuator/health  # user-service
curl http://localhost:8082/actuator/health  # order-service
curl http://localhost:8083/actuator/health  # weather-mcp-service
curl http://localhost:8084/actuator/health  # payment-service
curl http://localhost:3000                  # frontend
```

## 🔧 Environment Variables

### Backend Services

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPRING_PROFILES_ACTIVE` | Yes | `dev` | Active Spring profile (`dev`, `docker`, `prod`) |
| `SPRING_DATASOURCE_URL` | Yes | - | JDBC URL (e.g., `jdbc:postgresql://postgres:5432/testdb`) |
| `SPRING_DATASOURCE_USERNAME` | Yes | - | Database username |
| `SPRING_DATASOURCE_PASSWORD` | Yes | - | Database password |
| `SERVER_PORT` | No | Service-specific | HTTP port for the service |

### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | `http://localhost:8080` | Backend API base URL |
| `VITE_API_TIMEOUT` | No | `30000` | API request timeout (ms) |

### Docker Compose Environment

```yaml
environment:
  # PostgreSQL
  POSTGRES_DB: testdb
  POSTGRES_USER: testuser
  POSTGRES_PASSWORD: testpass
  
  # Backend
  SPRING_PROFILES_ACTIVE: docker
  SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/testdb
  SPRING_DATASOURCE_USERNAME: testuser
  SPRING_DATASOURCE_PASSWORD: testpass
  
  # Frontend
  VITE_API_URL: http://backend:8080
```

## 💻 Development Setup

### Backend Development

```bash
cd test-project/backend

# Build all services
mvn clean install

# Run individual service
cd user-service && mvn spring-boot:run

# Run tests
mvn test

# Run tests with coverage (user-service, order-service only)
mvn test jacoco:report

# Generate JAR
mvn package

# Access Swagger UI
# http://localhost:8081/swagger-ui.html (user-service)
# http://localhost:8082/swagger-ui.html (order-service)
# http://localhost:8083/swagger-ui.html (weather-mcp-service)
# http://localhost:8084/swagger-ui.html (payment-service)
```

### Frontend Development

```bash
cd test-project/frontend

# Install dependencies
npm install

# Start development server (with hot reload)
npm run dev

# Build for production
npm run build

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Preview production build
npm run preview
```

## 🧪 Testing

### Unit Tests (Backend)

```bash
# All services
cd test-project/backend && mvn test

# Specific service
cd user-service && mvn test

# With coverage
mvn test jacoco:report allure:serve
```

### E2E Tests (Playwright)

```bash
# From project root
cd /mnt/f/git/advanced
node run-ui-tests.js

# BDD feature files (steps not implemented yet)
# Located in: test-project/journeys/*.feature
```

### API Testing

```bash
# Health checks
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
curl http://localhost:8083/actuator/health
curl http://localhost:8084/actuator/health

# User service endpoints
curl http://localhost:8081/api/users
curl -X POST http://localhost:8081/api/users -H "Content-Type: application/json" -d '{"username":"test","email":"test@example.com"}'

# Order service endpoints
curl http://localhost:8082/api/orders

# Weather service endpoints
curl http://localhost:8083/api/weather

# Payment service endpoints
curl http://localhost:8084/api/payments
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :8081
lsof -i :3000
lsof -i :5432

# Kill the process
kill -9 <PID>

# Or change the port in application.properties / docker-compose.yaml
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs test-project-postgres

# Verify connection string
# Ensure SPRING_DATASOURCE_URL matches your PostgreSQL host/port

# Test connection
docker exec -it test-project-postgres psql -U testuser -d testdb
```

#### 3. Backend Service Won't Start

```bash
# Check Java version
java -version  # Should be Java 11+

# Check Maven
mvn -version

# Clean and rebuild
mvn clean install

# Check application logs
docker logs test-project-backend

# Verify database is accessible
docker exec -it test-project-backend ping postgres
```

#### 4. Frontend Can't Connect to Backend

```bash
# Check VITE_API_URL environment variable
cat test-project/frontend/.env

# Verify backend is accessible from frontend container
docker exec -it test-project-frontend curl http://backend:8080/actuator/health

# Check CORS configuration in backend
# Backend must allow requests from frontend origin
```

#### 5. Docker Compose Issues

```bash
# Remove all containers and volumes
docker-compose down -v

# Remove orphaned containers
docker-compose down --remove-orphans

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up

# Check Docker resources
docker system df
docker system prune
```

#### 6. Service Health Check Fails

```bash
# Check service logs
docker logs test-project-backend --tail 100

# Manually test health endpoint
docker exec -it test-project-backend curl http://localhost:8080/actuator/health

# Increase health check timeout in docker-compose.yaml
# healthcheck:
#   interval: 30s  # Increase from 10s
#   timeout: 10s   # Increase from 5s
#   retries: 10    # Increase from 5
```

#### 7. Frontend Build Errors

```bash
# Clear node_modules and cache
cd test-project/frontend
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Check TypeScript errors
npx tsc --noEmit

# Check for missing dependencies
npm outdated
npm audit fix
```

### Log Locations

```bash
# Docker logs
docker logs test-project-postgres
docker logs test-project-backend
docker logs test-project-frontend

# All logs combined
docker-compose logs -f

# Backend Maven logs
test-project/backend/*/target/*.log

# Frontend dev server logs
# Displayed in terminal where npm run dev is executed
```

### Performance Issues

```bash
# Check container resource usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory

# Optimize database queries
# Enable SQL logging: spring.jpa.show-sql=true
# Check slow query logs in PostgreSQL
```

## 📁 Project Structure

```
advanced/
├── README.md                    # This file
├── AGENTS.md                    # Agent configuration
├── run-ui-tests.js              # Playwright E2E test runner
├── .github/workflows/           # CI/CD pipelines
├── .opencode/                   # Opencode agent config
├── rules/                       # Documentation rules
│
└── test-project/
    ├── README.md                # Project-specific README
    ├── docker-compose.yaml      # Docker orchestration
    │
    ├── backend/                 # Spring Boot microservices
    │   ├── pom.xml              # Parent POM
    │   ├── user-service/        # Port 8081
    │   ├── order-service/       # Port 8082
    │   ├── weather-mcp-service/ # Port 8083
    │   └── payment-service/     # Port 8084
    │
    ├── frontend/                # React 18 + TypeScript + Vite
    │   ├── package.json
    │   ├── vite.config.ts
    │   └── src/
    │       ├── pages/           # 6 page components
    │       ├── components/      # Reusable components
    │       ├── context/         # Auth context
    │       └── api/             # API client
    │
    └── journeys/                # BDD feature files
        ├── *.feature            # Gherkin scenarios
        └── steps/               # (Empty - pending implementation)
```

## 📝 Additional Documentation

- [Backend Services README](./test-project/backend/README.md)
- [Frontend README](./test-project/frontend/README.md)
- [Docker Compose Configuration](./test-project/docker-compose.yaml)
- [CI/CD Workflows](./.github/workflows/)

## 🔗 Useful Links

- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [React Documentation](https://react.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Last Updated:** 2026-07-28  
**Version:** 1.0.0