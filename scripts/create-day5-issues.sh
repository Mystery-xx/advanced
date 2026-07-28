#!/bin/bash

# Day 5 Execution Loop - GitHub Issues Creator
# This script creates all 18 GitHub issues with proper labels and descriptions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Day 5 Execution Loop - Issue Creator${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Please install it first:"
    echo "  macOS: brew install gh"
    echo "  Linux: sudo apt install gh"
    echo "  Windows: winget install GitHub.cli"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Not authenticated with GitHub. Starting authentication...${NC}"
    gh auth login
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo -e "${RED}Error: Not in a GitHub repository or repository not accessible.${NC}"
    exit 1
fi

echo -e "${GREEN}Creating issues for repository: ${REPO}${NC}"
echo ""

# Function to create an issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"
    
    echo -e "${YELLOW}Creating: ${title}${NC}"
    
    # Create issue and capture the URL
    issue_url=$(gh issue create --title "$title" --body "$body" --label "$labels" --json url -q '.url' 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Created: ${issue_url}${NC}"
    else
        echo -e "${RED}✗ Failed to create issue${NC}"
    fi
    
    echo ""
}

# Issue 1
create_issue \
    "[BUG] Add @Valid annotation to UserController createUser endpoint" \
    "## Problem/Goal
The \`createUser\` endpoint in \`UserController\` is missing the \`@Valid\` annotation on the \`@RequestBody\` parameter, which means request body validation constraints (like \`@NotNull\`, \`@Email\`) are not being enforced.

## Files Affected
- \`test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java\`

## Acceptance Criteria
- [ ] Add \`@Valid\` annotation to the \`createUser\` method parameter
- [ ] Verify validation exceptions are properly handled
- [ ] Test with invalid request body (missing required fields, invalid email format)
- [ ] Ensure proper HTTP 400 responses with validation error messages

## Estimated Effort
S (Small)" \
    "bug,backend,user-service,validation"

# Issue 2
create_issue \
    "[FEATURE] Add pagination to GET /api/users endpoint" \
    "## Problem/Goal
The \`getAllUsers\` endpoint currently returns all users in a single response, which can cause performance issues with large datasets. Need to add pagination support.

## Files Affected
- \`test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java\`
- \`test-project/backend/user-service/src/main/java/com/example/userservice/service/UserService.java\`
- \`test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java\`

## Acceptance Criteria
- [ ] Add \`page\` (default: 0), \`size\` (default: 10), and \`sort\` (optional) query parameters
- [ ] Return paginated response with metadata (totalElements, totalPages, currentPage, etc.)
- [ ] Update service layer to use Spring Data JPA pagination
- [ ] Add unit tests for pagination logic
- [ ] Document new query parameters in API docs

## Estimated Effort
M (Medium)" \
    "feature,backend,user-service,api"

# Issue 3
create_issue \
    "[TEST] Write unit tests for UserServiceImpl" \
    "## Problem/Goal
The \`UserServiceImpl\` class lacks comprehensive unit tests. Need to add test coverage for core business logic methods.

## Files Affected
- \`test-project/backend/user-service/src/test/java/com/example/userservice/service/UserServiceImplTest.java\` (create)
- \`test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java\`

## Acceptance Criteria
- [ ] Test \`createUser\` method (success case, duplicate email, validation errors)
- [ ] Test \`getUserById\` method (found, not found)
- [ ] Test \`getAllUsers\` method (empty list, populated list)
- [ ] Test \`updateUser\` method (success, not found)
- [ ] Test \`deleteUser\` method (success, not found)
- [ ] Achieve minimum 80% code coverage for UserServiceImpl

## Estimated Effort
M (Medium)" \
    "test,backend,user-service"

# Issue 4
create_issue \
    "[BUG] Fix email uniqueness check - currently allows duplicate emails" \
    "## Problem/Goal
The current email uniqueness validation has a race condition or logic error that allows duplicate emails to be registered in the database.

## Files Affected
- \`test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java\`
- \`test-project/backend/user-service/src/main/java/com/example/userservice/repository/UserRepository.java\`

## Acceptance Criteria
- [ ] Add database constraint for email uniqueness (\`@Column(unique = true)\`)
- [ ] Fix service layer validation to check existing users properly
- [ ] Handle concurrent registration attempts gracefully
- [ ] Return appropriate error message when email already exists
- [ ] Add test case for duplicate email registration

## Estimated Effort
M (Medium)" \
    "bug,backend,user-service,database"

# Issue 5
create_issue \
    "[REFACTOR] Extract password validation logic to PasswordUtil class" \
    "## Problem/Goal
Password validation logic is currently embedded in the service layer, making it hard to reuse and test. Need to extract to a dedicated utility class.

## Files Affected
- \`test-project/backend/user-service/src/main/java/com/example/userservice/util/PasswordUtil.java\` (create)
- \`test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java\`

## Acceptance Criteria
- [ ] Create \`PasswordUtil\` class with \`validatePassword(String password)\` method
- [ ] Move password rules (min length, letters + numbers requirement) to utility
- [ ] Update \`UserServiceImpl\` to use the new utility class
- [ ] Add unit tests for \`PasswordUtil\`
- [ ] Ensure no functionality changes (backward compatible)

## Estimated Effort
S (Small)" \
    "refactor,backend,user-service,security"

# Issue 6
create_issue \
    "[DOC] Add JavaDoc to all UserController methods" \
    "## Problem/Goal
The \`UserController\` class lacks JavaDoc documentation, making it harder for developers to understand the API endpoints and their usage.

## Files Affected
- \`test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java\`

## Acceptance Criteria
- [ ] Add JavaDoc comments to all controller methods
- [ ] Document \`@param\` for each request parameter
- [ ] Document \`@return\` for response types
- [ ] Document \`@throws\` for exception cases
- [ ] Include example request/response in JavaDoc where applicable

## Estimated Effort
S (Small)" \
    "doc,backend,user-service"

# Issue 7
create_issue \
    "[FEATURE] Add order status history tracking" \
    "## Problem/Goal
Currently, order status changes are not tracked. Need to maintain a history of status changes with timestamps for audit and customer service purposes.

## Files Affected
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/model/OrderStatusHistory.java\` (create)
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/model/Order.java\`
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/service/OrderService.java\`
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/repository/OrderStatusHistoryRepository.java\` (create)

## Acceptance Criteria
- [ ] Create \`OrderStatusHistory\` entity with fields: id, orderId, oldStatus, newStatus, timestamp, changedBy
- [ ] Add relationship to \`Order\` entity (one-to-many)
- [ ] Update service layer to record status changes automatically
- [ ] Add endpoint to retrieve order status history: \`GET /api/orders/{id}/history\`
- [ ] Add migration script for existing orders
- [ ] Write unit and integration tests

## Estimated Effort
L (Large)" \
    "feature,backend,order-service,database"

# Issue 8
create_issue \
    "[TEST] Write integration tests for OrderController with MockMvc" \
    "## Problem/Goal
The \`OrderController\` lacks integration tests. Need to add comprehensive MockMvc tests to verify endpoint behavior.

## Files Affected
- \`test-project/backend/order-service/src/test/java/com/example/orderservice/controller/OrderControllerIntegrationTest.java\` (create)
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/controller/OrderController.java\`

## Acceptance Criteria
- [ ] Test \`GET /api/orders\` (empty list, populated list)
- [ ] Test \`GET /api/orders/{id}\` (found, not found)
- [ ] Test \`POST /api/orders\` (success, validation errors)
- [ ] Test \`PUT /api/orders/{id}/status\` (success, invalid status, not found)
- [ ] Test \`DELETE /api/orders/{id}\` (success, not found)
- [ ] Verify HTTP status codes and response structure
- [ ] Achieve minimum 80% controller coverage

## Estimated Effort
M (Medium)" \
    "test,backend,order-service"

# Issue 9
create_issue \
    "[BUG] Fix order cancellation - should not allow cancelling DELIVERED orders" \
    "## Problem/Goal
The order cancellation logic currently allows cancelling orders that have already been delivered, which violates business rules.

## Files Affected
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/service/OrderServiceImpl.java\`
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/model/OrderStatus.java\`

## Acceptance Criteria
- [ ] Add validation to prevent cancellation of DELIVERED orders
- [ ] Return appropriate error message (HTTP 400 or 409)
- [ ] Consider other invalid states (e.g., already CANCELLED)
- [ ] Add unit tests for cancellation logic
- [ ] Update API documentation with cancellation rules

## Estimated Effort
S (Small)" \
    "bug,backend,order-service,business-logic"

# Issue 10
create_issue \
    "[DOC] Add OpenAPI documentation for Order endpoints" \
    "## Problem/Goal
The Order Service lacks OpenAPI/Swagger documentation, making it difficult for frontend developers and API consumers to understand available endpoints.

## Files Affected
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/controller/OrderController.java\`
- \`test-project/backend/order-service/src/main/java/com/example/orderservice/model/\` (all model classes)
- \`test-project/backend/order-service/pom.xml\` (add springdoc-openapi dependency)

## Acceptance Criteria
- [ ] Add springdoc-openapi dependency to pom.xml
- [ ] Add \`@Operation\`, \`@ApiResponse\` annotations to all controller methods
- [ ] Add \`@Schema\` annotations to model classes
- [ ] Configure OpenAPI bean with service info
- [ ] Verify Swagger UI is accessible at \`/swagger-ui.html\`
- [ ] Test API documentation completeness

## Estimated Effort
M (Medium)" \
    "doc,backend,order-service,api"

# Issue 11
create_issue \
    "[BUG] Add client-side validation to registration form" \
    "## Problem/Goal
The registration form currently allows passwords without proper validation. Passwords must contain both letters and numbers for security compliance.

## Files Affected
- \`test-project/frontend/src/pages/Signup.tsx\`
- \`test-project/frontend/src/components/RegistrationForm.tsx\` (if exists)

## Acceptance Criteria
- [ ] Add password validation regex (must contain at least one letter and one number)
- [ ] Display real-time validation feedback to user
- [ ] Prevent form submission until password meets requirements
- [ ] Show clear error messages for invalid passwords
- [ ] Add visual indicators (checkmarks/x marks) for each requirement

## Estimated Effort
S (Small)" \
    "bug,frontend,validation,security"

# Issue 12
create_issue \
    "[FEATURE] Add loading states to all API calls" \
    "## Problem/Goal
The frontend currently lacks loading indicators during API calls, leading to poor user experience where users don't know if their action is being processed.

## Files Affected
- \`test-project/frontend/src/pages/Login.tsx\`
- \`test-project/frontend/src/pages/Signup.tsx\`
- \`test-project/frontend/src/pages/Dashboard.tsx\`
- \`test-project/frontend/src/pages/Orders.tsx\`
- \`test-project/frontend/src/pages/Weather.tsx\`
- \`test-project/frontend/src/components/Spinner.tsx\` (create)

## Acceptance Criteria
- [ ] Create reusable \`Spinner\` component
- [ ] Add loading state to login form submission
- [ ] Add loading state to registration form submission
- [ ] Add loading state to user list fetch on Dashboard
- [ ] Add loading state to order creation and status updates
- [ ] Add loading state to weather data fetch
- [ ] Ensure loading states are accessible (ARIA labels)

## Estimated Effort
M (Medium)" \
    "feature,frontend,ux"

# Issue 13
create_issue \
    "[TEST] Write E2E test for user registration flow with Playwright" \
    "## Problem/Goal
No E2E test coverage exists for the user registration flow. Need to add automated test to verify the complete registration process.

## Files Affected
- \`test-project/journeys/registration.feature\` (create or update)
- \`test-project/journeys/steps/registration.steps.ts\` (create)
- \`run-ui-tests.js\`

## Acceptance Criteria
- [ ] Create Gherkin feature file for registration scenario
- [ ] Implement step definitions using Playwright
- [ ] Test successful registration with valid data
- [ ] Test registration failure with duplicate email
- [ ] Test registration failure with invalid password
- [ ] Verify navigation to dashboard after successful registration
- [ ] Test runs in CI pipeline

## Estimated Effort
M (Medium \
    "test,frontend,e2e

# Issue 14
create_issue \
    "[REFACTOR] Extract API base URL to environment config file" \
    "## Problem/Goal
The API base URL is currently hardcoded in multiple files, making it difficult to switch between development, staging, and production environments.

## Files Affected
- \`test-project/frontend/src/services/api.ts\` (create)
- \`test-project/frontend/src/.env\` (create)
- \`test-project/frontend/src/.env.example\` (create)
- All files that make API calls

## Acceptance Criteria
- [ ] Create \`.env\` file with \`VITE_API_BASE_URL\` variable
- [ ] Create \`.env.example\` with placeholder values
- [ ] Create centralized API service using environment variable
- [ ] Update all API call sites to use the new service
- [ ] Add environment-specific configs (dev, staging, prod)
- [ ] Update README with environment setup instructions

## Estimated Effort
S (Small)" \
    "refactor,frontend,configuration"

# Issue 15
create_issue \
    "[TEST] Add E2E scenario for login → view users → logout flow" \
    "## Problem/Goal
Need comprehensive E2E test coverage for the core user journey: logging in, viewing the user list, and logging out.

## Files Affected
- \`test-project/journeys/user-flow.feature\` (create)
- \`test-project/journeys/steps/user-flow.steps.ts\` (create)

## Acceptance Criteria
- [ ] Create Gherkin feature file with scenario steps
- [ ] Implement step definitions for login
- [ ] Implement step definitions for viewing users on dashboard
- [ ] Implement step definitions for logout
- [ ] Verify user list is displayed correctly
- [ ] Test with valid credentials
- [ ] Add screenshot on failure for debugging

## Estimated Effort
M (Medium)" \
    "test,e2e,frontend,backend"

# Issue 16
create_issue \
    "[TEST] Add E2E scenario for creating order and verifying status change" \
    "## Problem/Goal
Need E2E test to verify the complete order creation flow and status update functionality.

## Files Affected
- \`test-project/journeys/order-flow.feature\` (create)
- \`test-project/journeys/steps/order-flow.steps.ts\` (create)

## Acceptance Criteria
- [ ] Create Gherkin feature file with order creation scenario
- [ ] Implement step definitions for navigating to orders page
- [ ] Implement step definitions for creating new order
- ] Implement step definitions for updating order
- [ ] Verify order appears in the order list
- [ ] Verify status change is reflected in UI
- [ Test validation errors (empty order, invalid data)

## Estimated Effort
M (Medium)" \
    "test,e2e,frontend,order-service"

# Issue 17
create_issue \
    "[DOC] Update README.md with current architecture diagram and port mapping" \
    "## Problem/Goal
The README.md is outdated and doesn't reflect the current architecture with 4 microservices, Docker Compose setup, and correct port mappings.

## Files Affected
- \`README.md\`
- \`test-project/README.md\`

## Acceptance Criteria
- [ ] Add architecture diagram (ASCII or image)
- [ ] Document all service ports: user-service (8081), order-service (8082), payment-service (8083), weather-mcp-service (8084), frontend (3000)
- [ ] Document PostgreSQL port (5432)
- [ ] Add Docker Compose setup instructions
- [ ] Add service startup sequence
- [ ] Document environment variables
- [ ] Add troubleshooting section

## Estimated Effort
M (Medium)" \
    "doc,infrastructure,setup"

# Issue 18
create_issue \
    "[DOC] Add API documentation with example requests/responses for each service" \
    "## Problem/Goal
Developers need comprehensive API documentation with example requests and responses for all four backend services to facilitate integration.

## Files Affected
- \`docs/api/README.md\` (create)
- \`docs/api/user-service.md\` (create)
- \`docs/api/order-service.md\` (create)
- \`docs/api/payment-service.md\` (create)
- \`docs/api/weather-mcp-service.md\` (create)

## Acceptance Criteria
- [ ] Document all User Service endpoints with examples
- [ ] Document all Order Service endpoints with examples
- [ ] Document all Payment Service endpoints with examples
- [ ] all Weather Service endpoints with examples
- [ ] Include curl examples for each endpoint
- [ ] Include example JSON request/response bodies
- [ ] Document error codes and messages
- [ ] Add authentication requirements

## Estimated Effort
L (Large)

## Related Issues
Related to Issue #10 (OpenAPI documentation)" \
    "doc,api,backend"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All 18 issues created successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "View all issues at: https://github.com/${REPO}/issues"