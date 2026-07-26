#!/bin/bash
set -e

echo "========================================="
echo "Test Project Setup Verification Script"
echo "========================================="
echo ""

PROJECT_ROOT="/mnt/f/git/advanced/test-project"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check directory structure
echo "1. Checking directory structure..."
[ -d "backend" ] && pass "backend/ directory exists" || fail "backend/ directory missing"
[ -d "frontend" ] && pass "frontend/ directory exists" || fail "frontend/ directory missing"
[ -d "backend/user-service" ] && pass "backend/user-service/ exists" || fail "backend/user-service/ missing"
[ -d "backend/order-service" ] && pass "backend/order-service/ exists" || fail "backend/order-service/ missing"
[ -d "backend/weather-mcp-service" ] && pass "backend/weather-mcp-service/ exists" || fail "backend/weather-mcp-service/ missing"
[ -d "backend/payment-service" ] && pass "backend/payment-service/ exists" || fail "backend/payment-service/ missing"
echo ""

# Check root pom.xml
echo "2. Checking root pom.xml..."
[ -f "pom.xml" ] && pass "pom.xml exists" || fail "pom.xml missing"
grep -q "spring-boot-starter-parent" pom.xml && pass "Spring Boot parent configured" || fail "Spring Boot parent not configured"
grep -q "java.version>17" pom.xml && pass "Java 17 configured" || fail "Java 17 not configured"
echo ""

# Check backend pom.xml
echo "3. Checking backend pom.xml..."
[ -f "backend/pom.xml" ] && pass "backend/pom.xml exists" || fail "backend/pom.xml missing"
grep -q "spring-boot-starter-web" backend/pom.xml && pass "spring-boot-starter-web included" || fail "spring-boot-starter-web missing"
grep -q "spring-boot-starter-data-jpa" backend/pom.xml && pass "spring-boot-starter-data-jpa included" || fail "spring-boot-starter-data-jpa missing"
grep -q "h2database" backend/pom.xml && pass "H2 database (test scope) included" || fail "H2 database missing"
echo ""

# Check service modules
echo "4. Checking service modules..."
for service in user-service order-service weather-mcp-service payment-service; do
    [ -f "backend/$service/pom.xml" ] && pass "$service/pom.xml exists" || fail "$service/pom.xml missing"
    [ -d "backend/$service/src/main/java" ] && pass "$service/src/main/java exists" || fail "$service/src/main/java missing"
    [ -f "backend/$service/src/main/resources/application.properties" ] && pass "$service/application.properties exists" || fail "$service/application.properties missing"
done
echo ""

# Check frontend
echo "5. Checking frontend..."
[ -f "frontend/package.json" ] && pass "frontend/package.json exists" || fail "frontend/package.json missing"
grep -q '"react":' frontend/package.json && pass "React dependency configured" || fail "React dependency missing"
grep -q '"vite":' frontend/package.json && pass "Vite dependency configured" || fail "Vite dependency missing"
grep -q '"typescript":' frontend/package.json && pass "TypeScript dependency configured" || fail "TypeScript dependency missing"
[ -f "frontend/tsconfig.json" ] && pass "tsconfig.json exists" || fail "tsconfig.json missing"
[ -f "frontend/vite.config.ts" ] && pass "vite.config.ts exists" || fail "vite.config.ts missing"
echo ""

# Check Docker Compose
echo "6. Checking Docker Compose..."
[ -f "docker-compose.yaml" ] && pass "docker-compose.yaml exists" || fail "docker-compose.yaml missing"
grep -q "postgres:15" docker-compose.yaml && pass "PostgreSQL 15 configured" || fail "PostgreSQL 15 not configured"
grep -q "8080:8080" docker-compose.yaml && pass "Backend port 8080 configured" || fail "Backend port not configured"
grep -q "3000" docker-compose.yaml && pass "Frontend port 3000 configured" || fail "Frontend port not configured"
echo ""

# Build verification
echo "7. Building backend (mvn clean compile)..."
cd backend
if mvn clean compile -q; then
    pass "Maven build successful"
else
    fail "Maven build failed"
fi
cd ..
echo ""

echo "8. Building frontend (npm run build)..."
cd frontend
if npm install --silent && npm run build --silent; then
    pass "NPM build successful"
else
    fail "NPM build failed"
fi
cd ..
echo ""

echo "========================================="
echo -e "${GREEN}All verification checks passed!${NC}"
echo "========================================="
echo ""
echo "Project Structure:"
echo "  - Backend: Spring Boot 3.4.1 + Java 17"
echo "  - Frontend: React 18 + Vite 5 + TypeScript 5"
echo "  - Database: PostgreSQL 15"
echo "  - Ports: Backend (8080), Frontend (3000), PostgreSQL (5432)"
echo ""
echo "Next steps:"
echo "  1. docker-compose up -d  (start all services)"
echo "  2. Access frontend at http://localhost:3000"
echo "  3. Access backend at http://localhost:8080"