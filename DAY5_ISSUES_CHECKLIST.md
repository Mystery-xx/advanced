# Day 5 Execution Loop - GitHub Issues Checklist

**Created:** 2026-07-28  
**Total Issues:** 18  
**Repository:** https://github.com/Mystery-xx/advanced

---

## Quick Status

- [ ] Issue #1: [BUG] Add @Valid annotation to UserController createUser endpoint
- [ ] Issue #2: [FEATURE] Add pagination to GET /api/users endpoint
- [ ] Issue #3: [TEST] Write unit tests for UserServiceImpl
- [ ] Issue #4: [BUG] Fix email uniqueness check
- [ ] Issue #5: [REFACTOR] Extract password validation logic to PasswordUtil class
- [ ] Issue #6: [DOC] Add JavaDoc to all UserController methods
- [ ] Issue #7: [FEATURE] Add order status history tracking
- [ ] Issue #8: [TEST] Write integration tests for OrderController with MockMvc
- [ ] Issue #9: [BUG] Fix order cancellation - should not allow cancelling DELIVERED orders
- [ ] Issue #10: [DOC] Add OpenAPI documentation for Order endpoints
- [ ] Issue #11: [BUG] Add client-side validation to registration form
- [ ] Issue #12: [FEATURE] Add loading states to all API calls
- [ ] Issue #13: [TEST] Write E2E test for user registration flow with Playwright
- [ ] Issue #14: [REFACTOR] Extract API base URL to environment config file
- [ ] Issue #15: [TEST] Add E2E scenario for login → view users → logout flow
- [ ] Issue #16: [TEST] Add E2E scenario for creating order and verifying status change
- [ ] Issue #17: [DOC] Update README.md with current architecture diagram and port mapping
- [ ] Issue #18: [DOC] Add API documentation with example requests/responses for each service

---

## Manual Creation Instructions

Since automated tools require GitHub API access, follow these steps to create issues manually:

### Step 1: Open GitHub Issues Page
Navigate to: https://github.com/Mystery-xx/advanced/issues

### Step 2: Create Each Issue
For each issue below:
1. Click "New Issue"
2. Copy the **Title** exactly as shown
3. Copy the **Description** into the description field
4. Add the **Labels** (create them if they don't exist)
5. Click "Submit new issue"

### Step 3: Verify Creation
After creating all 18 issues, verify:
- [ ] All 18 issues appear in the Issues list
- [ ] Each issue has the correct labels
- [ ] Each issue has acceptance criteria in the description
- [ ] Issue titles match the task list

---

## Labels to Create

Before creating issues, create these labels in GitHub (Settings → Labels):

**Type Labels:**
- `bug` - Red (#d73a4a)
- `feature` - Light Blue (#a2eeef)
- `test` - Yellow (#f9dd4b)
- `refactor` - Orange (#fbca04)
- `doc` - Blue (#0075ca)

**Component Labels:**
- `backend` - Purple (#5319e7)
- `frontend` - Blue (#0366d6)
- `e2e` - Light Blue (#c5def5)
- `infrastructure` - Blue (#0075ca)

**Service Labels:**
- `user-service` - Light Purple (#d4c5f9)
- `order-service` - Light Purple (#d4c5f9)
- `api` - Green (#c2e0c6)

**Other Labels:**
- `validation` - Green (#c2e0c6)
- `security` - Orange (#d93f0b)
- `ux` - Yellow (#fbca04)
- `database` - Green (#c2e0c6)
- `configuration` - Green (#c2e0c6)
- `setup` - Green (#c2e0c6)
- `business-logic` - Green (#c2e0c6)

---

## Issue Details for Manual Creation

### Issue 1
**Title:** `[BUG] Add @Valid annotation to UserController createUser endpoint`

**Labels:** `bug`, `backend`, `user-service`, `validation`

**Description:**
```
## Problem/Goal
The `createUser` endpoint in `UserController` is missing the `@Valid` annotation on the `@RequestBody` parameter, which means request body validation constraints (like `@NotNull`, `@Email`) are not being enforced.

## Files Affected
- test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java

## Acceptance Criteria
- [ ] Add `@Valid` annotation to the `createUser` method parameter
- [ ] Verify validation exceptions are properly handled
- [ ] Test with invalid request body (missing required fields, invalid email format)
- [ ] Ensure proper HTTP 400 responses with validation error messages

## Estimated Effort
S (Small)
```

---

### Issue 2
**Title:** `[FEATURE] Add pagination to GET /api/users endpoint`

**Labels:** `feature`, `backend`, `user-service`, `api`

**Description:**
```
## Problem/Goal
The `getAllUsers` endpoint currently returns all users in a single response, which can cause performance issues with large datasets. Need to add pagination support.

## Files Affected
- test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java
- test-project/backend/user-service/src/main/java/com/example/userservice/service/UserService.java
- test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java

## Acceptance Criteria
- [ ] Add `page` (default: 0), `size` (default: 10), and `sort` (optional) query parameters
- [ ] Return paginated response with metadata (totalElements, totalPages, currentPage, etc.)
- [ ] Update service layer to use Spring Data JPA pagination
- [ ] Add unit tests for pagination logic
- [ ] Document new query parameters in API docs

## Estimated Effort
M (Medium)
```

---

### Issue 3
**Title:** `[TEST] Write unit tests for UserServiceImpl`

**Labels:** `test`, `backend`, `user-service`

**Description:**
```
## Problem/Goal
The `UserServiceImpl` class lacks comprehensive unit tests. Need to add test coverage for core business logic methods.

## Files Affected
- test-project/backend/user-service/src/test/java/com/example/userservice/service/UserServiceImplTest.java (create)
- test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java

## Acceptance Criteria
- [ ] Test `createUser` method (success case, duplicate email, validation errors)
- [ ] Test `getUserById` method (found, not found)
- [ ] Test `getAllUsers` method (empty list, populated list)
- [ ] Test `updateUser` method (success, not found)
- [ ] Test `deleteUser` method (success, not found)
- [ ] Achieve minimum 80% code coverage for UserServiceImpl

## Estimated Effort
M (Medium)
```

---

### Issue 4
**Title:** `[BUG] Fix email uniqueness check - currently allows duplicate emails`

**Labels:** `bug`, `backend`, `user-service`, `database`

**Description:**
```
## Problem/Goal
The current email uniqueness validation has a race condition or logic error that allows duplicate emails to be registered in the database.

## Files Affected
- test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java
- test-project/backend/user-service/src/main/java/com/example/userservice/repository/UserRepository.java

## Acceptance Criteria
- [ ] Add database constraint for email uniqueness (`@Column(unique = true)`)
- [ ] Fix service layer validation to check existing users properly
- [ ] Handle concurrent registration attempts gracefully
- [ ] Return appropriate error message when email already exists
- [ ] Add test case for duplicate email registration

## Estimated Effort
M (Medium)
```

---

### Issue 5
**Title:** `[REFACTOR] Extract password validation logic to PasswordUtil class`

**Labels:** `refactor`, `backend`, `user-service`, `security`

**Description:**
```
## Problem/Goal
Password validation logic is currently embedded in the service layer, making it hard to reuse and test. Need to extract to a dedicated utility class.

## Files Affected
- test-project/backend/user-service/src/main/java/com/example/userservice/util/PasswordUtil.java (create)
- test-project/backend/user-service/src/main/java/com/example/userservice/service/UserServiceImpl.java

## Acceptance Criteria
- [ ] Create `PasswordUtil` class with `validatePassword(String password)` method
- [ ] Move password rules (min length, letters + numbers requirement) to utility
- [ ] Update `UserServiceImpl` to use the new utility class
- [ ] Add unit tests for `PasswordUtil`
- [ ] Ensure no functionality changes (backward compatible)

## Estimated Effort
S (Small)
```

---

### Issue 6
**Title:** `[DOC] Add JavaDoc to all UserController methods`

**Labels:** `doc`, `backend`, `user-service`

**Description:**
```
## Problem/Goal
The `UserController` class lacks JavaDoc documentation, making it harder for developers to understand the API endpoints and their usage.

## Files Affected
- test-project/backend/user-service/src/main/java/com/example/userservice/controller/UserController.java

## Acceptance Criteria
- [ ] Add JavaDoc comments to all controller methods
- [ ] Document `@param` for each request parameter
- [ ] Document `@return` for response types
- [ ] Document `@throws` for exception cases
- [ ] Include example request/response in JavaDoc where applicable

## Estimated Effort
S (Small)
```

---

### Issue 7
**Title:** `[FEATURE] Add order status history tracking`

**Labels:** `feature`, `backend`, `order-service`, `database`

**Description:**
```
## Problem/Goal
Currently, order status changes are not tracked. Need to maintain a history of status changes with timestamps for audit and customer service purposes.

## Files Affected
- test-project/backend/order-service/src/main/java/com/example/orderservice/model/OrderStatusHistory.java (create)
- test-project/backend/order-service/src/main/java/com/example/orderservice/model/Order.java
- test-project/backend/order-service/src/main/java/com/example/orderservice/service/OrderService.java
- test-project/backend/order-service/src/main/java/com/example/orderservice/repository/OrderStatusHistoryRepository.java (create)

## Acceptance Criteria
- [ ] Create `OrderStatusHistory` entity with fields: id, orderId, oldStatus, newStatus, timestamp, changedBy
- [ ] Add relationship to `Order` entity (one-to-many)
- [ ] Update service layer to record status changes automatically
- [ ] Add endpoint to retrieve order status history: GET /api/orders/{id}/history
- [ ] Add migration script for existing orders
- [ ] Write unit and integration tests

## Estimated Effort
L (Large)
```

---

### Issue 8
**Title:** `[TEST] Write integration tests for OrderController with MockMvc`

**Labels:** `test`, `backend`, `order-service`

**Description:**
```
## Problem/Goal
The `OrderController` lacks integration tests. Need to add comprehensive MockMvc tests to verify endpoint behavior.

## Files Affected
- test-project/backend/order-service/src/test/java/com/example/orderservice/controller/OrderControllerIntegrationTest.java (create)
- test-project/backend/order-service/src/main/java/com/example/orderservice/controller/OrderController.java

## Acceptance Criteria
- [ ] Test `GET /api/orders` (empty list, populated list)
- [ ] Test `GET /api/orders/{id}` (found, not found)
- [ ] Test `POST /api/orders` (success, validation errors)
- [ ] Test `PUT /api/orders/{id}/status` (success, invalid status, not found)
- [ ] Test `DELETE /api/orders/{id}` (success, not found)
- [ ] Verify HTTP status codes and response structure
- [ ] Achieve minimum 80% controller coverage

## Estimated Effort
M (Medium)
```

---

### Issue 9
**Title:** `[BUG] Fix order cancellation - should not allow cancelling DELIVERED orders`

**Labels:** `bug`, `backend`, `order-service`, `business-logic`

**Description:**
```
## Problem/Goal
The order cancellation logic currently allows cancelling orders that have already been delivered, which violates business rules.

## Files Affected
- test-project/backend/order-service/src/main/java/com/example/orderservice/service/OrderServiceImpl.java
- test-project/backend/order-service/src/main/java/com/example/orderservice/model/OrderStatus.java

## Acceptance Criteria
- [ ] Add validation to prevent cancellation of DELIVERED orders
- [ ] Return appropriate error message (HTTP 400 or 409)
- [ ] Consider other invalid states (e.g., already CANCELLED)
- [ ] Add unit tests for cancellation logic
- [ ] Update API documentation with cancellation rules

## Estimated Effort
S (Small)
```

---

### Issue 10
**Title:** `[DOC] Add OpenAPI documentation for Order endpoints`

**Labels:** `doc`, `backend`, `order-service`, `api`

**Description:**
```
## Problem/Goal
The Order Service lacks OpenAPI/Swagger documentation, making it difficult for frontend developers and API consumers to understand available endpoints.

## Files Affected
- test-project/backend/order-service/src/main/java/com/example/orderservice/controller/OrderController.java
- test-project/backend/order-service/src/main/java/com/example/orderservice/model/ (all model classes)
- test-project/backend/order-service/pom.xml (add springdoc-openapi dependency)

## Acceptance Criteria
- [ ] Add springdoc-openapi dependency to pom.xml
- [ ] Add `@Operation`, `@ApiResponse` annotations to all controller methods
- [ ] Add `@Schema` annotations to model classes
- [ ] Configure OpenAPI bean with service info
- [ ] Verify Swagger UI is accessible at `/swagger-ui.html`
- [ ] Test API documentation completeness

## Estimated Effort
M (Medium)
```

---

### Issue 11
**Title:** `[BUG] Add client-side validation to registration form`

**Labels:** `bug`, `frontend`, `validation`, `security`

**Description:**
```
## Problem/Goal
The registration form currently allows passwords without proper validation. Passwords must contain both letters and numbers for security compliance.

## Files Affected
- test-project/frontend/src/pages/Signup.tsx
- test-project/frontend/src/components/RegistrationForm.tsx (if exists)

## Acceptance Criteria
- [ ] Add password validation regex (must contain at least one letter and one number)
- [ ] Display real-time validation feedback to user
- [ ] Prevent form submission until password meets requirements
- [ ] Show clear error messages for invalid passwords
- [ ] Add visual indicators (checkmarks/x marks) for each requirement

## Estimated Effort
S (Small)
```

---

### Issue 12
**Title:** `[FEATURE] Add loading states to all API calls`

**Labels:** `feature`, `frontend`, `ux`

**Description:**
```
## Problem/Goal
The frontend currently lacks loading indicators during API calls, leading to poor user experience where users don't know if their action is being processed.

## Files Affected
- test-project/frontend/src/pages/Login.tsx
- test-project/frontend/src/pages/Signup.tsx
- test-project/frontend/src/pages/Dashboard.tsx
- test-project/frontend/src/pages/Orders.tsx
- test-project/frontend/src/pages/Weather.tsx
- test-project/frontend/src/components/Spinner.tsx (create)

## Acceptance Criteria
- [ ] Create reusable `Spinner` component
- [ ] Add loading state to login form submission
- [ ] Add loading state to registration form submission
- [ ] Add loading state to user list fetch on Dashboard
- [ ] Add loading state to order creation and status updates
- [ ] Add loading state to weather data fetch
- [ ] Ensure loading states are accessible (ARIA labels)

## Estimated Effort
M (Medium)
```

---

### Issue 13
**Title:** `[TEST] Write E2E test for user registration flow with Playwright`

**Labels:** `test`, `frontend`, `e2e`

**Description:**
```
## Problem/Goal
No E2E test coverage exists for the user registration flow. Need to add automated test to verify the complete registration process.

## Files Affected
- test-project/journeys/registration.feature (create or update)
- test-project/journeys/steps/registration.steps.ts (create)
- run-ui-tests.js

## Acceptance Criteria
- [ ] Create Gherkin feature file for registration scenario
- [ ] Implement step definitions using Playwright
- [ ] Test successful registration with valid data
- [ ] Test registration failure with duplicate email
- [ ] Test registration failure with invalid password
- [ ] Verify navigation to dashboard after successful registration
- [ ] Test runs in CI pipeline

## Estimated Effort
M (Medium)
```

---

### Issue 14
**Title:** `[REFACTOR] Extract API base URL to environment config file`

**Labels:** `refactor`, `frontend`, `configuration`

**Description:**
```
## Problem/Goal
The API base URL is currently hardcoded in multiple files, making it difficult to switch between development, staging, and production environments.

## Files Affected
- test-project/frontend/src/services/api.ts (create)
- test-project/frontend/src/.env (create)
- test-project/frontend/src/.env.example (create)
- All files that make API calls

## Acceptance Criteria
- [ ] Create `.env` file with `VITE_API_BASE_URL` variable
- [ ] Create `.env.example` with placeholder values
- [ ] Create centralized API service using environment variable
- [ ] Update all API call sites to use the new service
- [ ] Add environment-specific configs (dev, staging, prod)
- [ ] Update README with environment setup instructions

## Estimated Effort
S (Small)
```

---

### Issue 15
**Title:** `[TEST] Add E2E scenario for login → view users → logout flow`

**Labels:** `test`, `e2e`, `frontend`, `backend`

**Description:**
```
## Problem/Goal
Need comprehensive E2E test coverage for the core user journey: logging in, viewing the user list, and logging out.

## Files Affected
- test-project/journeys/user-flow.feature (create)
- test-project/journeys/steps/user-flow.steps.ts (create)

## Acceptance Criteria
- [ ] Create Gherkin feature file with scenario steps
- [ ] Implement step definitions for login
- [ ] Implement step definitions for viewing users on dashboard
- [ ] Implement step definitions for logout
- [ ] Verify user list is displayed correctly
- [ ] Test with valid credentials
- [ ] Add screenshot on failure for debugging

## Estimated Effort
M (Medium)
```

---

### Issue 16
**Title:** `[TEST] Add E2E scenario for creating order and verifying status change`

**Labels:** `test`, `e2e`, `frontend`, `order-service`

**Description:**
```
## Problem/Goal
Need E2E test to verify the complete order creation flow and status update functionality.

## Files Affected
- test-project/journeys/order-flow.feature (create)
- test-project/journeys/steps/order-flow.steps.ts (create)

## Acceptance Criteria
- [ ] Create Gherkin feature file with order creation scenario
- [ ] Implement step definitions for navigating to orders page
- [ ] Implement step definitions for creating new order
- [ ] Implement step definitions for updating order status
- [ ] Verify order appears in the order list
- [ ] Verify status change is reflected in UI
- [ ] Test validation errors (empty order, invalid data)

## Estimated Effort
M (Medium)
```

---

### Issue 17
**Title:** `[DOC] Update README.md with current architecture diagram and port mapping`

**Labels:** `doc`, `infrastructure`, `setup`

**Description:**
```
## Problem/Goal
The README.md is outdated and doesn't reflect the current architecture with 4 microservices, Docker Compose setup, and correct port mappings.

## Files Affected
- README.md
- test-project/README.md

## Acceptance Criteria
- [ ] Add architecture diagram (ASCII or image)
- [ ] Document all service ports: user-service (8081), order-service (8082), payment-service (8083), weather-mcp-service (8084), frontend (3000)
- [ ] Document PostgreSQL port (5432)
- [ ] Add Docker Compose setup instructions
- [ ] Add service startup sequence
- [ ] Document environment variables
- [ ] Add troubleshooting section

## Estimated Effort
M (Medium)
```

---

### Issue 18
**Title:** `[DOC] Add API documentation with example requests/responses for each service`

**Labels:** `doc`, `api`, `backend`

**Description:**
```
## Problem/Goal
Developers need comprehensive API documentation with example requests and responses for all four backend services to facilitate integration.

## Files Affected
- docs/api/README.md (create)
- docs/api/user-service.md (create)
- docs/api/order-service.md (create)
- docs/api/payment-service.md (create)
- docs/api/weather-mcp-service.md (create)

## Acceptance Criteria
- [ ] Document all User Service endpoints with examples
- [ ] Document all Order Service endpoints with examples
- [ ] Document all Payment Service endpoints with examples
- [ ] Document all Weather MCP Service endpoints with examples
- [ ] Include curl examples for each endpoint
- [ ] Include example JSON request/response bodies
- [ ] Document error codes and messages
- [ ] Add authentication requirements

## Estimated Effort
L (Large)

## Related Issues
Related to Issue #10 (OpenAPI documentation)
```

---

## Verification Checklist

After creating all issues, verify:

- [ ] 18 issues created on GitHub
- [ ] Each issue has correct labels (type + component + service)
- [ ] Each issue has description with acceptance criteria
- [ ] Each issue has estimated effort (S/M/L)
- [ ] Issues are trackable (can be referenced by number)
- [ ] All checkboxes in descriptions are clickable
- [ ] Links to files are valid (if repository is public)

---

## Files Reference

- `DAY5_ISSUES.md` - Complete issue documentation
- `DAY5_ISSUES_CHECKLIST.md` - This checklist (you are here)
- `scripts/create-issues.js` - Node.js automation script
- `scripts/create-day5-issues.sh` - Bash automation script
- `scripts/README-ISSUES.md` - Automation guide

---

## Next Steps

1. ✅ Create all 18 GitHub issues (use this checklist)
2. ⬜ Add issues to project board (if applicable)
3. ⬜ Assign team members to issues
4. ⬜ Set milestone (e.g., "Day 5 Sprint")
5. ⬜ Begin implementation work
6. ⬜ Track progress by checking off completed issues