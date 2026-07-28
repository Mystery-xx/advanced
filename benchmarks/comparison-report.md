# Cloud vs Local LLM Benchmark Comparison Report

**Date:** 2026-07-26  
**Models Compared:**
- Cloud: gpustack/default-coding (agentic with full tool access)
- Local: llama3.1:8b-instruct-q4_K_M via Ollama CLI (no tools)

---

## Executive Summary

This report compares the performance of a cloud-based coding LLM against a locally-hosted 8B parameter model across three real-world development tasks: bug fixing, architecture research, and code generation.

**Bottom line:** The local LLM completed tasks 16% faster but achieved only 33% pass rate versus 100% for the cloud model. Quality averaged 2.3/5 locally compared to 5.0/5 in the cloud. The local model is suitable for simple text transformations but fails at tasks requiring file access, multi-step reasoning, or complex instruction following.

**Recommendation:** Use cloud LLM for all agentic development work. Local LLM may serve for quick drafts, brainstorming, or offline scenarios where quality is not critical.

---

## Performance Metrics

### Speed Comparison

| Task | Cloud | Local | Difference |
|------|-------|-------|------------|
| Bug Fix | 55.3s | 65.9s | +19% slower |
| Research | 67.9s | 69.7s | +3% slower |
| Code Gen | 147.2s | 90.6s | -38% faster |
| **Total** | **270.4s** | **226.2s** | **-16% faster** |

The local model finished faster overall because it produced significantly less output on the code generation task (skeleton code vs full implementation).

### Quality Comparison

| Task | Cloud | Local | Gap |
|------|-------|-------|-----|
| Bug Fix | 5/5 | 3/5 | -40% |
| Research | 5/5 | 2/5 | -60% |
| Code Gen | 5/5 | 2/5 | -60% |
| **Average** | **5.0/5** | **2.3/5** | **-54%** |

### Pass Rate

| Metric | Cloud | Local |
|--------|-------|-------|
| Passed | 3/3 (100%) | 1/3 (33%) |
| Failed | 0/3 (0%) | 2/3 (67%) |

### Combined Scorecard

| Metric | Cloud | Local | Winner |
|--------|-------|-------|--------|
| Total Time | 270.4s | 226.2s | Local |
| Average Quality | 5.0/5 | 2.3/5 | Cloud |
| Pass Rate | 100% | 33% | Cloud |
| Instruction Following | Excellent | Poor | Cloud |
| File Access | Full | None | Cloud |

---

## Quality Metrics

### Task 1: Bug Fix

**Cloud (55.3s, 5/5, PASS):**
- Read both files (feature file + frontend)
- Made exactly 2 targeted edits
- Preserved original file structure
- Messages matched frontend exactly

**Local (65.9s, 3/5, PASS):**
- Identified correct error messages
- Ignored "no other changes" constraint
- Restructured entire feature file
- Generated new scenarios instead of editing existing ones

**Gap:** Local model understood the goal but failed to follow constraints.

---

### Task 2: Research

**Cloud (67.9s, 5/5, PASS):**
- Analyzed 6 actual files
- Listed 17 specific API endpoints
- Found critical `permitAll()` security gap
- Provided prioritized recommendations (Critical/High/Medium/Low)

**Local (69.7s, 2/5, FAIL):**
- Generic surface-level report
- Guessed 3 endpoint names (incorrect)
- Called SecurityConfig files "not provided" (they were in the task)
- Recommendations were boilerplate (OAuth, MFA) with no project grounding

**Gap:** Without file access, the local model hallucinated rather than analyzed.

---

### Task 3: Code Generation

**Cloud (147.2s, 5/5, PASS):**
- Created 400+ line file with 33 step definitions
- Regex patterns with {string} parameters
- Grouped by category (Auth, Admin, Navigation)
- Matched existing test runner style (Puppeteer-based)

**Local (90.6s, 2/5, FAIL):**
- Generated skeleton with ~10 placeholder steps
- Used wrong dependencies (`@cucumber/cucumber` vs project's Puppeteer)
- Steps contained `console.log` instead of real implementations
- Suggested splitting into multiple files (not requested)

**Gap:** Local model produced fast but unusable output.

---

## Root Cause Analysis

### Why Local LLM Failed

1. **No Tool Access**
   - Ran via `ollama run` CLI with zero file system access
   - Could not read source files, only process the prompt text
   - Result: hallucinated endpoints, guessed code structure

2. **Model Capacity**
   - 8B parameters vs likely 100B+ for cloud model
   - Insufficient capacity for multi-step reasoning
   - Struggled with complex constraints ("do X but not Y")

3. **Instruction Following**
   - Temperature 0.7 (CLI default) encouraged creative deviations
   - Restructured files when asked to preserve structure
   - Ignored explicit requirements (module.exports pattern, category grouping)

4. **No Agentic Loop**
   - Cloud model: read → analyze → edit → verify
   - Local model: single-pass text generation
   - No opportunity to correct mistakes or validate output

---

## Recommendations

### When to Use Cloud LLM

**Use cloud for:**
- Any task requiring file access or codebase understanding
- Research and architecture analysis
- Code generation that must integrate with existing code
- Bug fixes with specific constraints
- Tasks where correctness matters (production code, security)
- Multi-step workflows (read → edit → test → fix)

**Rationale:** 100% pass rate, 5/5 quality, follows complex instructions, grounded in actual code.

---

### When to Use Local LLM

**Use local for:**
- Quick drafts or brainstorming
- Simple text transformations (rewrite, summarize)
- Offline scenarios where cloud is unavailable
- Learning and experimentation (zero cost)
- First-pass code sketches to refine manually

**Rationale:** Fast, free, private. Acceptable for low-stakes work where you'll review and fix the output.

---

### When NOT to Use Local LLM

**Avoid local for:**
- Production code generation
- Security-sensitive analysis
- Tasks requiring file access or tool use
- Complex multi-constraint instructions
- Research requiring actual codebase investigation

**Rationale:** 67% failure rate, hallucinates without file access, ignores constraints.

---

## Cost-Benefit Analysis

| Factor | Cloud | Local |
|--------|-------|-------|
| Speed | Slower (270s) | Faster (226s) |
| Quality | 5.0/5 | 2.3/5 |
| Reliability | 100% pass | 33% pass |
| Cost | Per-token pricing | Free (your hardware) |
| Privacy | Data leaves machine | Fully local |
| Tool Access | Full (read/write/search) | None (CLI only) |

**Verdict:** Cloud LLM delivers 2.2x better quality with 100% reliability. Local LLM saves 44 seconds but produces output that requires significant manual correction or complete regeneration.

---

## Final Verdict

**Local LLM (llama3.1:8b-instruct-q4_K_M) is NOT a viable replacement for cloud-based agentic LLMs in development workflows.**

The 8B parameter model lacks:
- Capacity for grounded analysis without file access
- Ability to follow complex multi-part instructions
- Consistency needed for production work

**Recommended setup:**
- Primary: Cloud LLM for all serious development work
- Secondary: Local LLM for brainstorming, drafts, and offline scenarios

If local deployment is required for privacy or cost reasons, consider:
- Larger models (30B+ parameters) for better reasoning
- Tool integration (file access, search) via frameworks like Ollama + custom agent
- Lower temperature (0.2-0.4) for improved instruction following

---

## Appendix: Raw Data

### Cloud Baseline
- Task 1: 55.3s, 5/5, PASS
- Task 2: 67.9s, 5/5, PASS
- Task 3: 147.2s, 5/5, PASS
- **Total:** 270.4s, **Avg:** 5.0/5, **Pass:** 100%

### Local Results
- Task 1: 65.9s, 3/5, PASS
- Task 2: 69.7s, 2/5, FAIL
- Task 3: 90.6s, 2/5, FAIL
- **Total:** 226.2s, **Avg:** 2.3/5, **Pass:** 33%

**Sources:**
- `benchmarks/cloud-baseline.md`
- `benchmarks/local-results.md`