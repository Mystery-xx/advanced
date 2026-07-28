#!/bin/bash

# UI Test Runner Script
# This script runs the E2E tests with proper setup and validation

set -e

echo "=========================================="
echo "E2E UI Test Runner"
echo "=========================================="
echo ""

# Configuration
APP_URL="http://localhost:3000"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if frontend is running
echo "Checking if frontend is running at ${APP_URL}..."
if curl -s -o /dev/null -w "%{http_code}" "${APP_URL}" | grep -q "200\|304"; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${RED}✗ Frontend is not running at ${APP_URL}${NC}"
    echo ""
    echo "Please start the frontend:"
    echo "  cd test-project/frontend"
    echo "  npm run dev"
    echo ""
    echo "Or run with Docker Compose:"
    echo "  cd test-project"
    echo "  docker-compose up"
    exit 1
fi

# Check if Playwright is installed
echo ""
echo "Checking Playwright installation..."
if ! command -v npx &> /dev/null; then
    echo -e "${RED}✗ Node.js/npm is not installed${NC}"
    exit 1
fi

if ! npx playwright --version &> /dev/null; then
    echo -e "${YELLOW}⚠ Playwright is not installed. Installing...${NC}"
    npm install playwright
    npx playwright install chromium
fi

echo -e "${GREEN}✓ Playwright is ready${NC}"

# Run tests
echo ""
echo "=========================================="
echo "Running E2E Tests"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}"
node run-ui-tests.js

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "Tests completed successfully!"
    echo "==========================================${NC}"
    echo ""
    echo "View results:"
    echo "  - HTML Report: ${SCRIPT_DIR}/playwright-report/index.html"
    echo "  - Screenshots: ${SCRIPT_DIR}/playwright-report/screenshots/"
    echo ""
    
    # Try to open the report if xdg-open is available
    if command -v xdg-open &> /dev/null; then
        echo "Opening HTML report..."
        xdg-open "${SCRIPT_DIR}/playwright-report/index.html"
    fi
else
    echo ""
    echo -e "${RED}=========================================="
    echo "Tests failed!"
    echo "==========================================${NC}"
    echo ""
    echo "Check the HTML report for details:"
    echo "  ${SCRIPT_DIR}/playwright-report/index.html"
    exit 1
fi