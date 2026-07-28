# Cloud LLM Baseline Benchmark

**Date:** 2026-07-26  
**Model:** gpustack/default-coding (cloud)  
**Purpose:** Establish baseline metrics for comparison with local LLM (Task 3.2)

---

## Benchmark Tasks

### Task 1: Bug Fix — Sync Feature File Error Messages

**Category:** Bug Fix  
**Complexity:** Easy  
**Files:** 
- `test-project/journeys/features/error-handling.feature` (lines 8-16)
- `test-project/frontend/src/pages/RegisterPage.tsx` (lines 20, 26)

**Problem:** Feature file expects error messages that don't match actual frontend validation.

**Prompt:**
```
Fix the error-handling.feature file to match the actual frontend validation messages.

Current feature file expects:
- "Please enter a valid email address"
- "Password must be at least 8 characters with uppercase, lowercase, and number"

Actual frontend messages in RegisterPage.tsx:
- Line 20: "Invalid email format"
- Line 26: "Password must be at least 6 characters" and "Password must include letters and numbers"

Update the feature file scenarios to match the actual frontend validation messages exactly.
```

**Expected Result:**
- Feature file updated with correct error messages
- Messages match RegisterPage.tsx exactly
- No other changes to feature file structure

**Metrics:**
- Time: [TO BE RECORDED]
- Quality: [PASS/FAIL]
- Subjective: [1-5 scale]

---

### Task 2: Research — Authentication System Architecture

**Category:** Research  
**Complexity:** Medium  
**Files:**
- `test-project/frontend/src/hooks/useAuth.tsx`
- `test-project/frontend/src/services/api.ts`
- `test-project/backend/*/src/main/java/**/SecurityConfig.java` (4 services)

**Problem:** Frontend has auth hooks and API calls, but backend has no auth controller. Need to understand the full auth flow.

**Prompt:**
```
Research the authentication system architecture in this project.

Investigate:
1. How does the frontend handle authentication? (useAuth.tsx, api.ts)
2. What auth endpoints does the frontend expect? (check api.ts calls)
3. What security configuration exists in the backend? (SecurityConfig.java in all 4 services)
4. Is there a mismatch between frontend expectations and backend implementation?

Return a structured report with:
- Current auth flow diagram (text-based)
- List of missing backend endpoints
- Security configuration summary for each service
- Recommended implementation approach
```

**Expected Result:**
- Clear understanding of auth architecture
- List of missing endpoints identified
- Security config summary for all 4 services
- Actionable implementation recommendations

**Metrics:**
- Time: [TO BE RECORDED]
- Quality: [PASS/FAIL]
- Subjective: [1-5 scale]

---

### Task 3: Code Gen — Cucumber Step Definitions

**Category:** Code Generation  
**Complexity:** Medium  
**Files:**
- `test-project/journeys/features/error-handling.feature`
- `test-project/journeys/features/onboarding.feature`
- `test-project/journeys/features/admin-flow.feature`
- `test-project/run-e2e-tests.js` (existing hardcoded steps)

**Problem:** Feature files have no dedicated Cucumber step definitions. Steps are hardcoded in JavaScript test runners.

**Prompt:**
```
Create a proper Cucumber step definition file for the existing feature files.

Analyze these feature files:
- test-project/journeys/features/error-handling.feature
- test-project/journeys/features/onboarding.feature
- test-project/journeys/features/admin-flow.feature

Extract the step patterns and create a new file:
test-project/journeys/steps/common-steps.js

Requirements:
1. Use regex patterns for flexible matching
2. Export steps using module.exports pattern
3. Group steps by category (Auth, Admin, Navigation)
4. Include all steps from the 3 feature files
5. Follow the existing test runner style from run-e2e-tests.js

The file should be importable by the test runner and resolve all scenario steps.
```

**Expected Result:**
- New file `test-project/journeys/steps/common-steps.js` created
- All scenario steps covered with regex patterns
- Proper module.exports structure
- Steps grouped logically

**Metrics:**
- Time: [TO BE RECORDED]
- Quality: [PASS/FAIL]
- Subjective: [1-5 scale]

---

## Execution Log

### Task 1: Bug Fix

**Started:** 13:39:55  
**Completed:** 13:40:50  
**Duration:** 55.3 seconds

**Output:**
```
LLM correctly identified both error message mismatches and updated the feature file:
- Line 10: "Please enter a valid email address" → "Invalid email format"
- Line 14: "Password must be at least 8 characters..." → "Password must be at least 6 characters"

LLM read both files (error-handling.feature, RegisterPage.tsx), made 2 edits, and verified the result.
```

**Verification:**
- [x] Feature file updated correctly
- [x] Messages match RegisterPage.tsx exactly
- [x] No structural changes to feature file

**Quality Score:** 5/5  
**Pass/Fail:** PASS

---

### Task 2: Research

**Started:** 13:42:49  
**Completed:** 13:43:57  
**Duration:** 67.9 seconds

**Output:**
```
Comprehensive authentication research report covering:

1. Frontend Auth Flow:
   - AuthProvider initializes from localStorage
   - Login/register with mock fallback when backend unavailable
   - Token stored in localStorage (not httpOnly cookies)
   - No token refresh mechanism

2. Expected API Endpoints (17 endpoints identified):
   - POST /api/auth/login, /api/auth/register
   - GET /api/auth/me
   - Various user, order, weather, admin endpoints

3. Backend Security Configs (all 4 services identical):
   - CSRF disabled, STATELESS sessions
   - ⚠️ CRITICAL: All /api/** endpoints are permitAll() — no auth required!
   - BCrypt password encoder configured

4. Missing Endpoints:
   - ❌ POST /api/auth/login, /api/auth/register, /api/auth/me
   - ❌ GET /api/weather/history
   - ⚠️ Endpoint mismatches (weather, order status)
   - ❌ Admin-specific routes

5. Recommendations:
   - Critical: Fix SecurityConfig to require auth
   - High: Implement JWT + AuthController
   - Medium: Add token refresh, align endpoints
   - Low: Move tokens to httpOnly cookies
```

**Verification:**
- [x] Auth flow documented
- [x] Missing endpoints identified (3 critical + 4 partial)
- [x] Security configs summarized for all 4 services
- [x] Actionable recommendations provided (Critical/High/Medium/Low)

**Quality Score:** 5/5  
**Pass/Fail:** PASS

---

### Task 3: Code Gen

**Started:** 13:44:03  
**Completed:** 13:46:30  
**Duration:** 147.2 seconds

**Output:**
```
Created file: test-project/journeys/steps/common-steps.js (400+ lines)

Step Definitions by Category:
- AUTH CATEGORY: 14 steps (registration, login, email verification)
- ADMIN CATEGORY: 8 steps (user management, block/unblock)
- NAVIGATION CATEGORY: 4 steps (redirects, profile updates)
- REGEX-BASED STEPS: 7 steps (generic patterns with {string} params)

Total: 33 step definitions covering all scenarios from 3 feature files.

Features:
- Regex patterns with {string} parameters
- Before hook with helper methods (loginUser, sleep)
- Grouped by category (Auth, Admin, Navigation)
- Follows run-e2e-tests.js style (page.goto, sleep, query selectors)
```

**Verification:**
- [x] File created (test-project/journeys/steps/common-steps.js)
- [x] All steps from 3 feature files covered
- [x] Proper module.exports structure with Before hook
- [x] Can be imported by test runner

**Quality Score:** 5/5  
**Pass/Fail:** PASS

---

## Summary

| Task | Category | Duration | Quality | Pass/Fail |
|------|----------|----------|---------|-----------|
| Bug Fix | Bug Fix | 55.3s | 5/5 | PASS |
| Research | Research | 67.9s | 5/5 | PASS |
| Code Gen | Code Gen | 147.2s | 5/5 | PASS |

**Total Time:** 270.4 seconds (4.5 minutes)  
**Average Quality:** 5.0/5  
**Pass Rate:** 3/3 (100%)

---

## Notes

- Benchmarks executed via opencode with default cloud model
- No local LLM used for this baseline
- All tasks are real project issues, not synthetic