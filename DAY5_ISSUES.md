# Day 5 Execution Loop - GitHub Issues

This document contains 18 GitHub issues ready for creation. Each issue includes labels, description, acceptance criteria, and estimated effort.

---

## Backend - User Service (6 tasks)

### Issue 1: [BUG] Add @Valid annotation to UserController createUser endpoint

**Labels:** `bug`, `backend`, `user-service`, `validation`

**Problem/Goal:**
The `createUser` endpoint in `UserController` is missing the `@Valid` annotation on the `@RequestBody` parameter, which means request body validation constraints (like `@NotNull`, `@Email`) are not being enforced.

**Files Affected:**
- `test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java`

**Acceptance Criteria:**
- [ ] Add `@Valid` annotation to the `createUser` method parameter
- [ ] Verify validation exceptions are properly handled
- [ ] Test with invalid request body (missing required fields, invalid email format)
- [ ] Ensure proper HTTP 400 responses with validation error messages

**Estimated Effort:** S (Small)

**Related Issues:** None

---

### Issue 2: [FEATURE] Add pagination to GET /api/users endpoint

**Labels:** `feature`, `backend`, `user-service`, `api`

**Problem/Goal:**
The `getAllUsers` endpoint currently returns all users in a single response, which can cause performance issues with large datasets. Need to add pagination support.

**Files Affected:**
- `test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java`
- `test-project/backend/user-service/src/main/java/com/example/userservice/service/UserService.java`
- `test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java`

**Acceptance Criteria:**
- [ ] Add `page` (default: 0), `size` (default: 10), and `sort` (optional) query parameters
- [ ] Return paginated response with metadata (totalElements, totalPages, currentPage, etc.)
- [ ] Update service layer to use Spring Data JPA pagination
- [ ] Add unit tests for pagination logic
- [ ] Document new query parameters in API docs

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 3: [TEST] Write unit tests for UserServiceImpl

**Labels:** `test`, `backend`, `user-service`

**Problem/Goal:**
The `UserServiceImpl` class lacks comprehensive unit tests. Need to add test coverage for core business logic methods.

**Files Affected:**
- `test-project/backend/user-service/src/test/java/com/example/userservice/service/UserServiceImplTest.java` (create)
- `test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java`

**Acceptance Criteria:**
- [ ] Test `createUser` method (success case, duplicate email, validation errors)
- [ ] Test `getUserById` method (found, not found)
- [ ] Test `getAllUsers` method (empty list, populated list)
- [ ] Test `updateUser` method (success, not found)
- [ ] Test `deleteUser` method (success, not found)
- [ ] Achieve minimum 80% code coverage for UserServiceImpl

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 4: [BUG] Fix email uniqueness check - currently allows duplicate emails

**Labels:** `bug`, `backend`, `user-service`, `database`

**Problem/Goal:**
The current email uniqueness validation has a race condition or logic error that allows duplicate emails to be registered in the database.

**Files Affected:**
- `test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java`
- `test-project/backend/user-service/src/main/java/com/example/userservice/repository/UserRepository.java`

**Acceptance Criteria:**
- [ ] Add database constraint for email uniqueness (`@Column(unique = true)`)
- [ ] Fix service layer validation to check existing users properly
- [ ] Handle concurrent registration attempts gracefully
- [ ] Return appropriate error message when email already exists
- [ ] Add test case for duplicate email registration

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 5: [REFACTOR] Extract password validation logic to PasswordUtil class

**Labels:** `refactor`, `backend`, `user-service`, `security`

**Problem/Goal:**
Password validation logic is currently embedded in the service layer, making it hard to reuse and test. Need to extract to a dedicated utility class.

**Files Affected:**
- `test-project/backend/user-service/src/main/java/com/example/userservice/util/PasswordUtil.java` (create)
- `test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java`

**Acceptance Criteria:**
- [ ] Create `PasswordUtil` class with `validatePassword(String password)` method
- [ ] Move password rules (min length, letters + numbers requirement) to utility
- [ ] Update `UserServiceImpl` to use the new utility class
- [ ] Add unit tests for `PasswordUtil`
- [ ] Ensure no functionality changes (backward compatible)

**Estimated Effort:** S (Small)

**Related Issues:** None

---

### Issue 6: [DOC] Add JavaDoc to all UserController methods

**Labels:** `doc`, `backend`, `user-service`

**Problem/Goal:**
The `UserController` class lacks JavaDoc documentation, making it harder for developers to understand the API endpoints and their usage.

**Files Affected:**
- `test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java`

**Acceptance Criteria:**
- [ ] Add JavaDoc comments to all controller methods
- [ ] Document `@param` for each request parameter
- [ ] Document `@return` for response types
- [ ] Document `@throws` for exception cases
- [ ] Include example request/response in JavaDoc where applicable

**Estimated Effort:** S (Small)

**Related Issues:** None

---

## Backend - Order Service (4 tasks)

### Issue 7: [FEATURE] Add order status history tracking

**Labels:** `feature`, `backend`, `order-service`, `database`

**Problem/Goal:**
Currently, order status changes are not tracked. Need to maintain a history of status changes with timestamps for audit and customer service purposes.

**Files Affected:**
- `test-project/backend/order-service/src/main/java/com/example/orderservice/model/OrderStatusHistory.java` (create)
- `test-project/backend/order-service/src/main/java/com/example/orderservice/model/Order.java`
- `test-project/backend/order-service/src/main/java/com/example/orderservice/service/OrderService.java`
- `test-project/backend/order-service/src/main/java/com/example/orderservice/repository/OrderStatusHistoryRepository.java` (create)

**Acceptance Criteria:**
- [ ] Create `OrderStatusHistory` entity with fields: id, orderId, oldStatus, newStatus, timestamp, changedBy
- [ ] Add relationship to `Order` entity (one-to-many)
- [ ] Update service layer to record status changes automatically
- [ ] Add endpoint to retrieve order status history: `GET /api/orders/{id}/history`
- [ ] Add migration script for existing orders
- [ ] Write unit and integration tests

**Estimated Effort:** L (Large)

**Related Issues:** None

---

### Issue 8: [TEST] Write integration tests for OrderController with MockMvc

**Labels:** `test`, `backend`, `order-service`

**Problem/Goal:**
The `OrderController` lacks integration tests. Need to add comprehensive MockMvc tests to verify endpoint behavior.

**Files Affected:**
- `test-project/backend/order-service/src/test/java/com/example/orderservice/controller/OrderControllerIntegrationTest.java` (create)
- `test-project/backend/order-service/src/main/java/com/example/orderservice/controller/OrderController.java`

**Acceptance Criteria:**
- [ ] Test `GET /api/orders` (empty list, populated list)
- [ ] Test `GET /api/orders/{id}` (found, not found)
- [ ] Test `POST /api/orders` (success, validation errors)
- [ ] Test `PUT /api/orders/{id}/status` (success, invalid status, not found)
- [ ] Test `DELETE /api/orders/{id}` (success, not found)
- [ ] Verify HTTP status codes and response structure
- [ ] Achieve minimum 80% controller coverage

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 9: [BUG] Fix order cancellation - should not allow cancelling DELIVERED orders

**Labels:** `bug`, `backend`, `order-service`, `business-logic`

**Problem/Goal:**
The order cancellation logic currently allows cancelling orders that have already been delivered, which violates business rules.

**Files Affected:**
- `test-project/backend/order-service/src/main/java/com/example/orderservice/service/OrderServiceImpl.java`
- `test-project/backend/order-service/src/main/java/com/example/orderservice/model/OrderStatus.java`

**Acceptance Criteria:**
- [ ] Add validation to prevent cancellation of DELIVERED orders
- [ ] Return appropriate error message (HTTP 400 or 409)
- [ ] Consider other invalid states (e.g., already CANCELLED)
- [ ] Add unit tests for cancellation logic
- [ ] Update API documentation with cancellation rules

**Estimated Effort:** S (Small)

**Related Issues:** None

---

### Issue 10: [DOC] Add OpenAPI documentation for Order endpoints

**Labels:** `doc`, `backend`, `order-service`, `api`

**Problem/Goal:**
The Order Service lacks OpenAPI/Swagger documentation, making it difficult for frontend developers and API consumers to understand available endpoints.

**Files Affected:**
- `test-project/backend/order-service/src/main/java/com/example/orderservice/controller/OrderController.java`
- `test-project/backend/order-service/src/main/java/com/example/orderservice/model/` (all model classes)
- `test-project/backend/order-service/pom.xml` (add springdoc-openapi dependency)

**Acceptance Criteria:**
- [ ] Add springdoc-openapi dependency to pom.xml
- [ ] Add `@Operation`, `@ApiResponse` annotations to all controller methods
- [ ] Add `@Schema` annotations to model classes
- [ ] Configure OpenAPI bean with service info
- [ ] Verify Swagger UI is accessible at `/swagger-ui.html`
- [ ] Test API documentation completeness

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

## Frontend (4 tasks)

### Issue 11: [BUG] Add client-side validation to registration form

**Labels:** `bug`, `frontend`, `validation`, `security`

**Problem/Goal:**
The registration form currently allows passwords without proper validation. Passwords must contain both letters and numbers for security compliance.

**Files Affected:**
- `test-project/frontend/src/pages/Signup.tsx`
- `test-project/frontend/src/components/RegistrationForm.tsx` (if exists)

**Acceptance Criteria:**
- [ ] Add password validation regex (must contain at least one letter and one number)
- [ ] Display real-time validation feedback to user
- [ ] Prevent form submission until password meets requirements
- [ ] Show clear error messages for invalid passwords
- [ ] Add visual indicators (checkmarks/x marks) for each requirement

**Estimated Effort:** S (Small)

**Related Issues:** None

---

### Issue 12: [FEATURE] Add loading states to all API calls

**Labels:** `feature`, `frontend`, `ux`

**Problem/Goal:**
The frontend currently lacks loading indicators during API calls, leading to poor user experience where users don't know if their action is being processed.

**Files Affected:**
- `test-project/frontend/src/pages/Login.tsx`
- `test-project/frontend/src/pages/Signup.tsx`
- `test-project/frontend/src/pages/Dashboard.tsx`
- `test-project/frontend/src/pages/Orders.tsx`
- `test-project/frontend/src/pages/Weather.tsx`
- `test-project/frontend/src/components/Spinner.tsx` (create)

**Acceptance Criteria:**
- [ ] Create reusable `Spinner` component
- [ ] Add loading state to login form submission
- [ ] Add loading state to registration form submission
- [ ] Add loading state to user list fetch on Dashboard
- [ ] Add loading state to order creation and status updates
- [ ] Add loading state to weather data fetch
- [ ] Ensure loading states are accessible (ARIA labels)

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 13: [TEST] Write E2E test for user registration flow with Playwright

**Labels:** `test`, `frontend`, `e2e`

**Problem/Goal:**
No E2E test coverage exists for the user registration flow. Need to add automated test to verify the complete registration process.

**Files Affected:**
- `test-project/jouneys/registration.feature` (create or update)
- `test-project/jouneys/steps/registration.steps.ts` (create)
- `run-ui-tests.js`

**Acceptance Criteria:**
- [ ] Create Gherkin feature file for registration scenario
- [ ] Implement step definitions using Playwright
- [ ] Test successful registration with valid data
- [ ] Test registration failure with duplicate email
- [ ] Test registration failure with invalid password
- [ ] Verify navigation to dashboard after successful registration
- [ ] Test runs in CI pipeline

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 14: [REFACTOR] Extract API base URL to environment config file

**Labels:** `refactor`, `frontend`, `configuration`

**Problem/Goal:**
The API base URL is currently hardcoded in multiple files, making it difficult to switch between development, staging, and production environments.

**Files Affected:**
- `test-project/frontend/src/services/api.ts` (create)
- `test-project/frontend/src/.env` (create)
- `test-project/frontend/src/.env.example` (create)
- All files that make API calls

**Acceptance Criteria:**
- [ ] Create `.env` file with `VITE_API_BASE_URL` variable
- [ ] Create `.env.example` with placeholder values
- [ ] Create centralized API service using environment variable
- [ ] Update all API call sites to use the new service
- [ ] Add environment-specific configs (dev, staging, prod)
- [ ] Update README with environment setup instructions

**Estimated Effort:** S (Small)

**Related Issues:** None

---

## Tests & E2E (2 tasks)

### Issue 15: [TEST] Add E2E scenario for login → view users → logout flow

**Labels:** `test`, `e2e`, `frontend`, `backend`

**Problem/Goal:**
Need comprehensive E2E test coverage for the core user journey: logging in, viewing the user list, and logging out.

**Files Affected:**
- `test-project/jouneys/user-flow.feature` (create)
- `test-project/jouneys/steps/user-flow.steps.ts` (create)

**Acceptance Criteria:**
- [ ] Create Gherkin feature file with scenario steps
- [ ] Implement step definitions for login
- [ ] Implement step definitions for viewing users on dashboard
- [ ] Implement step definitions for logout
- [ ] Verify user list is displayed correctly
- [ ] Test with valid credentials
- [ ] Add screenshot on failure for debugging

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 16: [TEST] Add E2E scenario for creating order and verifying status change

**Labels:** `test`, `e2e`, `frontend`, `order-service`

**Problem/Goal:**
Need E2E test to verify the complete order creation flow and status update functionality.

**Files Affected:**
- `test-project/jouneys/order-flow.feature` (create)
- `test-project/jouneys/steps/order-flow.steps.ts` (create)

**Acceptance Criteria:**
- [ ] Create Gherkin feature file with order creation scenario
- [ ] Implement step definitions for navigating to orders page
- [ ] Implement step definitions for creating a new order
- [ ] Implement step definitions for updating order status
- [ ] Verify order appears in the order list
- [ ] Verify status change is reflected in UI
- [ ] Test validation errors (empty order, invalid data)

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

## Documentation (2 tasks)

### Issue 17: [DOC] Update README.md with current architecture diagram and port mapping

**Labels:** `doc`, `infrastructure`, `setup`

**Problem/Goal:**
The README.md is outdated and doesn't reflect the current architecture with 4 microservices, Docker Compose setup, and correct port mappings.

**Files Affected:**
- `README.md`
- `test-project/README.md`

**Acceptance Criteria:**
- [ ] Add architecture diagram (ASCII or image)
- [ ] Document all service ports: user-service (8081), order-service (8082), payment-service (8083), weather-mcp-service (8084), frontend (3000)
- [ ] Document PostgreSQL port (5432)
- [ ] Add Docker Compose setup instructions
- [ ] Add service startup sequence
- [ ] Document environment variables
- [ ] Add troubleshooting section

**Estimated Effort:** M (Medium)

**Related Issues:** None

---

### Issue 18: [DOC] Add API documentation with example requests/responses for each service

**Labels:** `doc`, `api`, `backend`

**Problem/Goal:**
Developers need comprehensive API documentation with example requests and responses for all four backend services to facilitate integration.

**Files Affected:**
- `docs/api/README.md` (create)
- `docs/api/user-service.md` (create)
- `docs/api/order-service.md` (create)
- `docs/api/payment-service.md` (create)
- `docs/api/weather-mcp-service.md` (create)

**Acceptance Criteria:**
- [ ] Document all User Service endpoints with examples
- [ ] Document all Order Service endpoints with examples
- [ ] Document all Payment Service endpoints with examples
- [ ] Document all Weather MCP Service endpoints with examples
- [ ] Include curl examples for each endpoint
- [ ] Include example JSON request/response bodies
- [ ] Document error codes and messages
- [ ] Add authentication requirements

**Estimated Effort:** L (Large)

**Related Issues:** Related to Issue #10 (OpenAPI documentation)

---

## Summary

| # | Label | Service | Task | Effort |
|---|-------|---------|------|--------|
| 1 | bug | user-service | Add @Valid annotation | S |
| 2 | feature | user-service | Add pagination | M |
| 3 | test | user-service | Write unit tests | M |
| 4 | bug | user-service | Fix email uniqueness | M |
| 5 | refactor | user-service | Extract PasswordUtil | S |
| 6 | doc | user-service | Add JavaDoc | S |
| 7 | feature | order-service | Status history tracking | L |
| 8 | test | order-service | MockMvc integration tests | M |
| 9 | bug | order-service | Fix order cancellation | S |
| 10 | doc | order-service | OpenAPI documentation | M |
| 11 | bug | frontend | Registration validation | S |
| 12 | feature | frontend | Loading states | M |
| 13 | test | frontend | Registration E2E test | M |
| 14 | refactor | frontend | API config extraction | S |
| 15 | test | e2e | Login→View→Logout flow | M |
| 16 | test | e2e | Order creation flow | M |
| 17 | doc | docs | Update README | M |
| 18 | doc | docs | API documentation | L |

**Total Effort:** 6S + 9M + 2L = ~30 story points

---

## Quick Create Commands

Once GitHub CLI is installed and authenticated, run:

```bash
# Install gh CLI (if needed)
# macOS: brew install gh
# Linux: sudo apt install gh
# Windows: winget install GitHub.cli

# Authenticate
gh auth login

# Create all issues
gh issue create --title "[BUG] Add @Valid annotation to UserController createUser endpoint" --body-file issues/issue-1.md --label bug,backend,user-service
# ... repeat for all 18 issues
```

Or use the provided script at `scripts/create-issues.sh` (to be created).