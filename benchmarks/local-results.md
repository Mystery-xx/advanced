# Local LLM Benchmark Results

**Date:** 2026-07-26  
**Model:** llama3.1:8b-instruct-q4_K_M (Ollama CLI)  
**Purpose:** Run 3 benchmark tasks on local LLM via Ollama CLI for comparison with cloud baseline

---

## Benchmark Tasks

### Task 1: Bug Fix — Sync Feature File Error Messages

**Category:** Bug Fix  
**Complexity:** Easy  
**Run via:** `ollama run llama3.1:8b-instruct-q4_K_M` (CLI, no agent)

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
- Time: 65.9s
- Quality: PASS
- Subjective: 3/5

**Result:**
The local LLM identified the correct error messages ("Invalid email format", "Password must be at least 6 characters", "Password must include letters and numbers") but did not edit the existing feature file. Instead, it generated a completely new feature file (3 separate scenarios) with different structure and syntax than the original. The original file structure was not preserved.

**Comparison to Cloud:**
- Cloud: 55.3s, 5/5 — Edited the existing file preserving structure, only changed error messages
- Local: 65.9s, 3/5 — Identified correct messages but restructured the entire file (did not follow "no other changes" instruction)

---

### Task 2: Research — Authentication System Architecture

**Category:** Research  
**Complexity:** Medium  
**Run via:** `ollama run llama3.1:8b-instruct-q4_K_M` (CLI, no agent)

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
- Time: 69.7s
- Quality: FAIL
- Subjective: 2/5

**Result:**
The local LLM produced a very generic, surface-level report. It acknowledged the existence of `SecurityConfig.java` files and the `useAuth` hook/`api.ts`, but did not reference any actual code or specific endpoints. Key findings:
- Identified 3 expected endpoints (login, register, forgot-password) — but guessed blindly, did not inspect actual files
- No specific endpoint URLs listed
- No actual SecurityConfig.java details (called them "not provided" despite being part of the task)
- Generic recommendations (OAuth, bcrypt, MFA) without project-specific grounding
- Did NOT discover the critical `permitAll()` security gap that the cloud model found

**Comparison to Cloud:**
- Cloud: 67.9s, 5/5 — Found 17 actual endpoints, identified the critical `permitAll()` security gap, listed exact mismatches
- Local: 69.7s, 2/5 — Generic report with no file-level detail, missed critical security issues, made up endpoint names

---

### Task 3: Code Gen — Cucumber Step Definitions

**Category:** Code Generation  
**Complexity:** Medium  
**Run via:** `ollama run llama3.1:8b-instruct-q4_K_M` (CLI, no agent)

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
- Time: 90.6s
- Quality: FAIL
- Subjective: 2/5

**Result:**
The local LLM generated a JavaScript file with some step structure but:
- Used `@cucumber/cucumber` requires (not the project's existing Puppeteer-based test runner style)
- Created generic placeholder steps with `console.log` — no actual implementation
- Did not extract real step patterns from the 3 feature files
- Generated very few steps (~10) vs the 33 steps the cloud model produced
- Suggested splitting into separate files (auth-steps.js, admin-steps.js, navigation-steps.js) — not what was asked
- Did not follow the existing `run-e2e-tests.js` style (which uses `page.goto`, `sleep`, query selectors)

**Comparison to Cloud:**
- Cloud: 147.2s, 5/5 — Created a full 400+ line file with 33 real step definitions, proper regex patterns, Before hook, category grouping, matching project style
- Local: 90.6s, 2/5 — Created a skeleton with placeholders, wrong dependencies, minimal coverage, did not follow project patterns

---

## Summary

| Task | Category | Duration | Quality | Pass/Fail |
|------|----------|----------|---------|-----------|
| Bug Fix | Bug Fix | 65.9s | 3/5 | PASS |
| Research | Research | 69.7s | 2/5 | FAIL |
| Code Gen | Code Gen | 90.6s | 2/5 | FAIL |

**Total Time:** 226.2 seconds (3.8 minutes)  
**Average Quality:** 2.3/5  
**Pass Rate:** 1/3 (33%)

---

## Analysis

### Speed Comparison (Cloud vs Local)

| Task | Cloud | Local | Delta |
|------|-------|-------|-------|
| Bug Fix | 55.3s | 65.9s | +10.6s (+19%) |
| Research | 67.9s | 69.7s | +1.8s (+3%) |
| Code Gen | 147.2s | 90.6s | -56.6s (-38%) |
| **Total** | **270.4s** | **226.2s** | **-44.2s (-16%)** |

Local LLM was faster in total time, primarily because the code gen task produced a much smaller output. However, **quality was drastically worse**.

### Quality Comparison

| Task | Cloud | Local | Delta |
|------|-------|-------|-------|
| Bug Fix | 5/5 | 3/5 | -2 |
| Research | 5/5 | 2/5 | -3 |
| Code Gen | 5/5 | 2/5 | -3 |
| **Average** | **5.0/5** | **2.3/5** | **-2.7** |

### Pass Rate

| Metric | Cloud | Local |
|--------|-------|-------|
| Pass | 3/3 (100%) | 1/3 (33%) |
| Fail | 0/3 (0%) | 2/3 (67%) |

### Key Observations

1. **Instruction following is weak**: Local LLM frequently ignored "no other changes" constraints and restructured outputs
2. **No file access = hallucination**: Without file-reading tools, the local LLM guessed endpoints and code structure
3. **Research suffers most**: The 8B model cannot produce deep, grounded analysis without actual file access
4. **Code gen is fast but shallow**: Local LLM is quicker but produces skeleton code vs full implementations
5. **Bug fix is viable**: The only task that partially succeeded — correct error messages identified, but structure not preserved
6. **CLI-only limitation**: Running via `ollama run` provides zero tools (no file system access, no context) — unlike the cloud model which had full read/write + search capabilities

### Verdict

**Local LLM (llama3.1:8b-instruct-q4_K_M) is NOT a replacement for the cloud model in agentic tasks.** It can handle simple text transformations but fails at research and code generation that require file access, multi-step reasoning, or following complex constraints. The 8B parameter model lacks the capacity for grounded, tool-using agent behavior.

The temperature 0.7 (CLI default) likely contributed to creative deviations from instructions. Lower temperatures may improve instruction following for the Bug Fix task.
