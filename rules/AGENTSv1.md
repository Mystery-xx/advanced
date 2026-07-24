# AGENTS.md — Leroy Merlin Russia PlatformECO BFF Autotests

**Project Type**: Kotlin/Cucumber BDD API Test Framework (Test-Only, Zero Production Code)  
**Domain**: BFF (Backend-For-Frontend) Definitions Validation  
**Stack**: Kotlin 1.9+, Maven Multi-Module, Cucumber JVM, TestNG, WireMock, Redis, Docker  
**Core Dependency**: `autotests-core v2.5.5` (external shared library)

---

## Quick Start

```bash
# Run all tests
mvn clean test

# Run specific module
mvn clean test -pl ucc

# Run specific feature
mvn test -Dcucumber.filter.tags="@ucc and @Smoke"

# Local Docker setup
docker-compose up -d  # Uses docker-compose.yaml
```

---

## Project Structure

```
lmru--pao--platformeco--bff--autotests/
├── pom.xml                          # Root POM (aggregates 5 modules)
├── README.md                        # 827 lines — comprehensive guide
├── docker-compose.yaml              # Main Docker setup (WireMock, Redis)
├── docker-compose222.yml            # Alternative config (port 222)
├── Jenkinsfile*                     # 4 variants at root (legacy)
├── .codegraph/                      # Codegraph index (should be gitignored)
├── bff/                             # Orphan: nginx proxy config (NOT test infra)
│
├── ucc/                             # LARGEST module (~69 features, 60% of tests)
│   ├── src/test/kotlin/ru/leroymerlin/ucc/
│   │   ├── TestRunner.kt            # Cucumber TestNG runner
│   │   ├── UccSteps.kt              # Step definitions + RedisService
│   │   ├── mocks/                   # WireMock stubs
│   │   ├── requests/                # Request builders
│   │   └── responses/               # Response models
│   └── src/test/resources/ucc/features/
│
├── omnicart/                        # Second largest, has Redis steps
│   ├── src/test/kotlin/ru/leroymerlin/omnicart/
│   │   ├── TestRunner.kt
│   │   ├── OmnicartSteps.kt         # + RedisService (DUPLICATE)
│   │   └── ...
│   └── src/test/resources/omnicart/features/
│
├── pao/                             # INCOMPLETE: no TestRunner, empty PaoSteps
│   ├── src/test/kotlin/ru/leroymerlin/pao/
│   │   └── PaoSteps.kt              # Empty shell
│   └── src/test/resources/pao/features/
│
├── payment/                         # Standard structure, empty custom steps
│   └── src/test/kotlin/ru/leroymerlin/payment/
│       └── PaymentSteps.kt          # Empty
│
└── shoppinglist/                    # ⚠️ PACKAGE TYPO: ru.leruymerlin (missing 'o')
    └── src/test/kotlin/ru/leruymerlin/  # Should be ru.leroymerlin
        └── ShoppingListSteps.kt     # Empty
```

---

## Test Architecture

### Mandatory Scenario Types (Per Feature File)

Every `.feature` file MUST contain these 3 scenario categories:

1. **Validation Errors** (`@ValidationErrors`) — Invalid input, 400/422 responses
2. **Backend Errors** (`@BackendErrors`) — Downstream failures, 502/503/504 from mocks
3. **Positive Cases** (`@Positive`) — Happy path, valid responses

### Mandatory `description` Column in Examples Tables

**Rule**: Every Examples table MUST have a `description` column with meaningful test case documentation.

```gherkin
# ✅ CORRECT: description column present and populated
Примеры:
  | branch  | statusCode | description                    |
  | branch1 | 500        | Cart service unavailable       |
  | branch2 | 503        | Backend timeout                |

# ❌ WRONG: missing description column
Примеры:
  | branch  | statusCode |
  | branch1 | 500        |
  | branch2 | 503        |
```

**Requirements**:
- Column MUST be named exactly `description` (last column)
- Values MUST describe what the test case validates (not just "test 1", "test 2")
- For parametrized scenarios (`Структура сценария`), the description value MUST be interpolated into the scenario name:

```gherkin
# ✅ CORRECT: description from table is in scenario name
Структура сценария: Проверка ошибок сервисов - <description>
  ...
  Примеры:
    | branch  | description                    |
    | branch1 | Cart service unavailable       |
    | branch2 | Backend timeout                |

# ❌ WRONG: scenario name doesn't use <description>
Структура сценария: Проверка ошибок сервисов
  ...
```

**Why**: The `description` column serves as living documentation for test coverage reports and helps identify failing tests without reading the full scenario.

### Table Formatting Rules

**CRITICAL**: When modifying feature files, ALWAYS preserve table formatting:

```gherkin
# ✅ CORRECT: Aligned columns, consistent spacing
Примеры:
  | branch   | statusCode | code | message                    |
  | branch1  | 500        | 175  | Cart service unavailable   |
  | branch2  | 503        | 184  | Backend timeout            |

# ❌ WRONG: Misaligned columns, inconsistent spacing
Примеры:
  | branch | statusCode | code | message |
  | branch1 | 500 | 175 | Cart service unavailable |
  | branch2|503|184|Backend timeout|
```

**Rules**:
1. Use pipe `|` delimiters with single space padding: `| value |`
2. Align column widths to the longest value in each column
3. NEVER remove columns without explicit permission (especially `description`)
4. Keep table header separator line: `|---|---|---|`
5. Use 6-space indentation for tables inside scenarios
6. Column borders MUST align vertically (all `|` characters in a column must be on the same vertical line)
7. Pad short values with spaces to match the longest value in the column
8. Long values in one column do NOT affect spacing of other columns

**Example with long values**:
```gherkin
# ✅ CORRECT: All | borders aligned vertically
Примеры:
  | header            | value      | message                                                                            |
  | front-application | MagPortal1 | headers/front-application must match pattern "^(MagPortal\|MagMobile)$"            |
  | channel           | OFFLINE2   | headers/channel must match pattern "^(OFFLINE\|ONLINE\|CC)$"                       |
  | device-type       | 6          | headers/device-type must match pattern "^(0\|1\|2\|3\|4\|5)$"                      |

# ❌ WRONG: Borders not aligned
Примеры:
  | header | value | message |
  | front-application | MagPortal1 | headers/front-application must match pattern "^(MagPortal\|MagMobile)$" |
  | channel | OFFLINE2 | headers/channel must match pattern "^(OFFLINE\|ONLINE\|CC)$" |
```

**Why**: Properly formatted tables are easier to read, review, and maintain. Misaligned tables cause diff noise and review confusion.

### Branch-Based Mock Parametrization

Tests run against different backend branches using status-code suffixed mock files:

```gherkin
Дано инициализировать заглушки для ветки "feature-branch"
# Loads: mocks/{feature-branch}_200.json, mocks/{feature-branch}_502.json, etc.
```

**File Naming Convention**: `{branchName}_{statusCode}.json`

### WireMock Stub Requirements

All stubs MUST validate incoming parameters:

```kotlin
// GOOD: Validates request body
stubFor(post(urlEqualTo("/api/endpoint"))
    .withRequestBody(matchingJsonPath("$.userId"))
    .willReturn(aResponse().withStatus(200)))

// BAD: No validation
stubFor(post(urlEqualTo("/api/endpoint"))
    .willReturn(aResponse().withStatus(200)))
```

### Custom Steps Pattern (Guice DI)

```kotlin
@Inject lateinit var testContext: TestContext
@Inject lateinit var wireMockServer: WireMockServer

// Access shared state
testContext.set("userId", "12345")
val userId = testContext.get<String>("userId")
```

---

## Known Issues & TODOs

### Critical

| Issue | Severity | Module | Status |
|-------|----------|--------|--------|
| Package typo: `ru.leruymerlin` | High | shoppinglist | **BLOCKING** — glue scanning may fail |
| Missing TestRunner.kt | High | pao | Tests cannot execute |
| Empty Steps classes | Medium | pao, payment, shoppinglist | No custom step logic |
| RedisService duplicated | Medium | ucc, omnicart | Should extract to core |

### Technical Debt

- **9 TODOs** in codebase:
  - Legacy feature file to delete: `no_servicePromiseId`
  - Commented-out test branches 8 & 9 (cleanup candidate)
  - Unimplemented scenarios marked `isRemoved=true`
  - Duplicated `responseBodyEqualTo` logic → extract to core

### Config Issues

- Root POM declares `src/main/kotlin` but no main source exists
- 4 flat Jenkinsfiles at root (non-standard, should be in `.jenkins/`)
- `.codegraph/*.db` committed (should be in `.gitignore`)
- Orphan `bff/` directory (nginx config, not test infra — consider deletion)

---

## Modules & Tags Reference

### Module-to-Tag Mapping

| Module | Directory | Tags | Component | Description |
|--------|-----------|------|-----------|-------------|
| **checkouts/** | `ucc/src/test/resources/features/checkouts/` | `@united_middle` | Checkout | Оформление заказа (корзина, доставка, оплата) |
| **carts/** | `ucc/src/test/resources/features/carts/` | `@united_middle` | Carts | Управление корзинами |
| **cma/** | `ucc/src/test/resources/features/cma/` | `@united_middle` | CMA | Click & Collect / Express доставка |
| **mobile/** | `ucc/src/test/resources/features/mobile/` | `@mobile_bff`, `@bff_mobile` | Mobile BFF | Эндпоинты для мобильного приложения |
| **services/** | `ucc/src/test/resources/features/services/` | `@united_middle` | Services | Услуги в корзине |
| **kz/** | `ucc/src/test/resources/features/kz/` | `@united_middle` | KZ | Казахстан (локализация) |
| **typ/** | `ucc/src/test/resources/features/typ/` | `@united_middle` | TYPL | Типовые сценарии |

### Tag Categories

**BFF Scope Tags:**
- `@united_middle` — **Единый BFF** (Checkout + Carts + CMA + Services + KZ + TYPL). Все компоненты одного миддл-слоя для веб и мобильного каналов
- `@mobile_bff`, `@bff_mobile` — Мобильный BFF (специфичные эндпоинты только для mobile)

> **Важно:** `@united_middle` — это НЕ отдельные BFF на каждый модуль, а **один общий BFF**, который покрывает все компоненты: checkout, корзина, CMA, услуги, KZ, типовые сценарии. Изменения в логике BFF затрагивают все модули с этим тегом.

**Functional Tags:**
- `@carts_v3`, `@carts_ucc2` — Версии API корзин
- `@get_cart`, `@patch_carts`, `@post_carts` — Конкретные ручки
- `@checkout_post_v2`, `@fulfillment_options_get_v` — Эндпоинты checkout

**Test Type Tags:**
- `@ValidationErrors` — Тесты валидации (400/422)
- `@BackendErrors` — Тесты ошибок бекенда (500/502/503/504)
- `@Positive` — Позитивные сценарии
- `@Smoke` — Критичные тесты для CI

### CRITICAL: Verify Scope Before Changes

**MANDATORY workflow for task-based changes (e.g., PAO-XXXX):**

```bash
# 1. ALWAYS check which files have the relevant tag BEFORE making changes
grep -r "@united_middle" --include="*.feature" -l
grep -r "@mobile_bff" --include="*.feature" -l

# 2. Verify with user if scope is unclear
# Example: "Task PAO-10570 affects BFF Checkout. Should I change:"
# - Only checkouts/ (37 files)?
# - All @united_middle modules (69 files)?

# 3. NEVER assume scope based on "BFF" keyword alone
# Different modules = different BFF services
```

### FORBIDDEN: Changing Mock Data
When changing expected BFF response codes (e.g., 503→500):
- NEVER change mock file names (`503_error`, `503_238`) — these are backend mocks
- NEVER change mock configuration tables — these define what the backend returns, not what BFF responds
- ONLY change `| statusCode |` column in Examples tables and `возвращается статус код` lines

### FORBIDDEN: Script-Generated Binary Files
The script `scripts/validate_tables.py` uses `\x00` placeholder for `\|` patterns:
- ALWAYS verify the script restores `\|` after processing
- CHECK files for NUL symbols after running: `grep -c $'\x00' *.feature` (should be 0)
- NUL symbols make `.feature` files appear as binary to git

### FORBIDDEN: Force Push Without Warning
- `git push --force` can silently overwrite user changes
- Use `git push --force-with-lease` instead (safer)
- Warn before any force push

**Common Mistake to Avoid:**
> ❌ "Задача про BFF → меняю только checkouts/"  
> ✅ "Задача про BFF → проверяю тег `@united_middle` → меняю ВСЕ модули с этим тегом (checkouts/, carts/, cma/, services/, kz/, typ/)"

**Example from PAO-10570:**
- Task: Change BFF response 503→500 on backend errors
- Initial mistake: Changed only checkouts/, missed carts/, cma/, services/, kz/, typ/
- Correct scope: ALL 69 files with `@united_middle` tag (единый BFF)
- Excluded: mobile/ (has `@mobile_bff`, not `@united_middle`)

---

## Module Details

### ucc (Priority: HIGH)

**Largest module** — 69 features, ~60% of all tests

**Key Patterns**:
- Full Redis integration via `RedisService.kt`
- Comprehensive mock coverage (200, 400, 502, 503, 504)
- Branch-based testing fully implemented

**When to modify**:
- Adding new BFF endpoints
- Updating validation rules
- Extending Redis test scenarios

### omnicart (Priority: MEDIUM)

**Second largest** — similar structure to ucc

**Key Patterns**:
- Duplicates `RedisService.kt` from ucc (refactor candidate)
- Cart-specific business logic

**When to modify**:
- Cart operation changes
- Redis cache invalidation tests

### pao (Priority: LOW — INCOMPLETE)

**Status**: Non-functional — missing TestRunner, empty Steps

**Action Required**:
1. Create `TestRunner.kt` (copy from ucc)
2. Implement `PaoSteps.kt` with PAO-specific logic
3. Add suite.xml configuration

### payment (Priority: MEDIUM)

**Status**: Functional but minimal custom steps

**When to modify**:
- Payment flow changes
- New payment provider integration tests

### shoppinglist (Priority: HIGH — BLOCKING BUG)

**Status**: Functional but **PACKAGE TYPO**

**Action Required**:
1. Rename directory: `ru/leruymerlin/` → `ru/leroymerlin/`
2. Update package declarations in all `.kt` files
3. Verify glue scanning works post-fix

---

## Development Workflows

### Adding a New Feature File

```bash
# 1. Create feature file with mandatory scenario types
touch src/test/resources/{module}/features/NewFeature.feature

# 2. Add Gherkin structure
cat > src/test/resources/{module}/features/NewFeature.feature <<EOF
#language: ru

Функционал: New Feature Name

@ValidationErrors
Сценарий: Invalid input returns 400
  ...

@BackendErrors
Сценарий: Backend unavailable returns 502
  ...

@Positive
Сценарий: Valid request returns 200
  ...
EOF

# 3. Add corresponding mocks
touch src/test/kotlin/{module}/mocks/default_200.json
touch src/test/kotlin/{module}/mocks/default_502.json

# 4. Run tests
mvn test -Dcucumber.filter.tags="@{module} and @NewFeature"
```

### Adding Custom Step Definitions

```kotlin
// In {Module}Steps.kt
@Inject lateinit var testContext: TestContext

@Когда("^пользователь делает запрос с параметрами (.+)$")
fun makeRequestWithParams(params: String) {
    val response = wireMockServer.stubFor(...)
    testContext.set("lastResponse", response)
}

@Тогда("^ответ содержит поле (.+) со значением (.+)$")
fun responseContainsField(field: String, value: String) {
    val response = testContext.get<String>("lastResponse")
    // Validation logic
}
```

### Running Tests

```bash
# All tests
mvn clean test

# Single module
mvn test -pl ucc

# Single feature file
mvn test -Dcucumber.filter.tags="@ucc and @features/my-feature.feature"

# By tag
mvn test -Dcucumber.filter.tags="@Smoke"
mvn test -Dcucumber.filter.tags="@ValidationErrors"

# With Docker cleanup
docker-compose down -v && docker-compose up -d && mvn clean test
```

---

## External Dependencies

### autotests-core v2.5.5

**Shared library** providing:
- Base test runner configuration
- WireMock integration
- Redis client wrapper
- Guice DI setup
- Common step definitions

**DO NOT** override core functionality unless absolutely necessary.

### WireMock

**Port**: 8080 (default), 222 (alternative config)  
**Stub Location**: `src/test/kotlin/{module}/mocks/`  
**Recording**: Use WireMock Admin API to record stubs from live BFF

### Redis

**Port**: 6379  
**Usage**: Cache validation, session state  
**Modules with Redis**: ucc, omnicart (pao/payment/shoppinglist do NOT use Redis)

---

## Quality Gates

### Pre-Commit Checklist

- [ ] Feature file has all 3 mandatory scenario types
- [ ] Mocks validate incoming parameters (bodyPatterns, queryParameters)
- [ ] Package names match `ru.leroymerlin.{module}` (watch for typos)
- [ ] No TODOs introduced without tracking issue
- [ ] `mvn test` passes locally with Docker running

### LSP Diagnostics

**Kotlin Language Server**: NOT INSTALLED (0/42 LSP servers active)  
**Recommendation**: Install kotlin-ls for type checking and navigation

```bash
# Check LSP status
lsp_status
```

---

## Agent Guidelines

### When Modifying This Codebase

1. **READ FIRST**: Use `codegraph_explore` to find existing patterns before writing new code
2. **MATCH STYLE**: Follow existing step definition patterns (Guice DI, testContext usage)
3. **RESPECT MODULE BOUNDARIES**: Do not cross-import between modules
4. **TEST COVERAGE**: Every new scenario needs validation + backend error + positive cases
5. **MOCK VALIDATION**: WireMock stubs MUST validate request parameters

### Delegation Strategy

| Task Type | Agent | Skills |
|-----------|-------|--------|
| Add feature file + steps | `deep` | `cucumber-gherkin` |
| Refactor RedisService duplication | `deep` | `programming` |
| Fix package typo | `quick` | (none) |
| Add pao TestRunner | `deep` | `programming` |
| Security audit | `oracle` | `security-research` |
| Visual QA (N/A — API only) | — | — |

### Forbidden Actions

- **NEVER** suppress type errors with `as any` or `@ts-ignore` (N/A for Kotlin, but use `!!` sparingly)
- **NEVER** commit `.codegraph/*.db` files
- **NEVER** delete failing tests to "pass" CI
- **NEVER** add new Jenkinsfiles at root (use `.jenkins/` if needed)
- **NEVER** introduce new modules updating root POM

---

## Session Continuity

**Active Background Tasks**: Track via `task_list`  
**Continuation IDs**: Store `ses_...` from `task()` output for follow-ups  
**Compression**: Use `compress` after each major phase (discovery, implementation, verification)

---

## Contact & Escalation

**Project Owner**: Leroy Merlin Russia PlatformECO Team  
**Core Library**: `autotests-core` (external dependency)  
**Documentation**: README.md (827 lines — read before making architectural changes)

---

**Last Updated**: 2026-07-23  
**Generated By**: /init-deep skill (Sisyphus agent)  
**Next Review**: After fixing shoppinglist package typo and pao TestRunner