# Command: update-scenarios

## Trigger

**Команда:** `/update-scenarios`

**Альтернативный триггер:** Пользователь просит "обнови сценарии" или "sync сценарии со Swagger"

**Описание:** Автоматическое сканирование Swagger API backend'а и обновление `.feature` файлов в `journeys/features/` для соответствия актуальным endpoint'ам.

## Usage

```bash
# Полная синхронизация всех сценариев
/update-scenarios

# Синхронизация конкретного сценария
/update-scenarios --feature=order-flow.feature

# Dry-run (без записи изменений)
/update-scenarios --dry-run
```

## Prerequisites

**Перед запуском убедись:**

1. **Backend запущен и доступен:**
   ```bash
   # Проверка доступности Swagger
   curl http://localhost:8080/v3/api-docs
   # или для отдельных сервисов:
   curl http://localhost:8081/v3/api-docs  # user-service
   curl http://localhost:8082/v3/api-docs  # order-service
   curl http://localhost:8083/v3/api-docs  # weather-mcp-service
   curl http://localhost:8084/v3/api-docs  # payment-service
   ```

2. **Сценарии существуют:**
   - Файлы `journeys/features/*.feature` существуют
   - Gherkin синтаксис валиден

3. **State ledger доступен:**
   - Файл `.omo/state/testing-assignment.json` существует

## Execution Flow

### 1. Pre-flight checks

**Проверка состояния Level 1:**
```json
// Читай .omo/state/testing-assignment.json
{
  "level1": { "status": "pending|running|passed|failed" }
}
```

**Conditional routing:**
- **ЕСЛИ Level 1.status = "failed"**:
  ```
  ⚠️ Level 1 тесты не пройдены. Пропуск обновления сценариев.
  Recommendation: Запусти /run-level1-tests сначала.
  ```
  **СТОП.** Не продолжай до Level 2.

- **ЕСЛИ Level 1.status = "passed"**:
  Продолжай синхронизацию.

### 2. Сканирование Swagger

**Для каждого сервиса (4 total):**

```bash
# 1. Fetch Swagger JSON
curl http://localhost:{PORT}/v3/api-docs > swagger-{service}.json

# 2. Извлеки endpoints
# - paths: все доступные route'ы
# - methods: GET, POST, PUT, DELETE
# - request/response schemas
```

**Сравни с текущими сценариями:**
- Какие endpoint'ы есть в Swagger но не покрыты в `.feature`?
- Какие endpoint'ы устарели (удалены/изменены)?
- Какие параметры изменились (новые required поля)?

### 3. Обновление .feature файлов

**Для каждого сценария:**

1. **onboarding.feature** → сверь с `user-service` endpoints:
   - POST /users (registration)
   - GET /users/{id} (profile)
   - PUT /users/{id} (update profile)

2. **order-flow.feature** → сверь с `order-service` endpoints:
   - POST /orders (create order)
   - GET /orders/{id} (get order)
   - PUT /orders/{id}/status (update status)

3. **admin-flow.feature** → сверь с `user-service` admin endpoints:
   - GET /admin/users (list all users)
   - PUT /admin/users/{id}/block (block user)
   - PUT /admin/users/{id}/unblock (unblock user)

4. **weather-dashboard.feature** → сверь с `weather-mcp-service`:
   - GET /weather/current (current weather)
   - POST /weather/alerts (create alert)
   - GET /weather/alerts (list alerts)

5. **error-handling.feature** → проверь validation schemas:
   - Email format validation
   - Password strength requirements
   - Required field checks

**Формат обновлений:**
- Добавляй новые шаги для endpoint'ов без покрытия
- Обновляй существующие шаги с изменёнными параметрами
- Помечай удалённые endpoint'ы комментарием `# DEPRECATED: removed in API v{version}`

### 4. Валидация

**Dry-run режим:**
```bash
# Покажи diff без записи
npx cucumber-js --dry-run journeys/features/*.feature
```

**Полная валидация:**
```bash
# Проверка синтаксиса
npx cucumber-js journeys/features/*.feature --dry-run

# Проверка state ledger
cat .omo/state/testing-assignment.json
```

### 5. Обновление State Ledger

**Запиши артефакты:**
```json
{
  "level2": {
    "status": "pending",
    "lastRun": "2026-07-25T12:34:56Z",
    "artifacts": [
      "journeys/features/onboarding.feature",
      "journeys/features/order-flow.feature",
      "journeys/features/admin-flow.feature",
      "journeys/features/weather-dashboard.feature",
      "journeys/features/error-handling.feature"
    ]
  },
  "artifacts": [
    "journeys/features/*.feature (updated)"
  ],
  "lastUpdated": "2026-07-25T12:34:56Z"
}
```

## Output

**Консольный вывод:**
```
Scanning Swagger endpoints...
✓ user-service: 8 endpoints found
✓ order-service: 6 endpoints found
✓ weather-mcp-service: 5 endpoints found
✓ payment-service: 4 endpoints found

Comparing with existing scenarios...
✓ onboarding.feature: 2 steps updated
✓ order-flow.feature: no changes needed
✓ admin-flow.feature: 1 step added
✓ weather-dashboard.feature: no changes needed
✓ error-handling.feature: no changes needed

State ledger updated: .omo/state/testing-assignment.json

Ready for Level 2 tests. Run /run-level2-journeys
```

**Артефакты после выполнения:**
```
journeys/features/
├── onboarding.feature (updated)
├── order-flow.feature
├── admin-flow.feature (updated)
├── weather-dashboard.feature
└── error-handling.feature

.omo/state/
└── testing-assignment.json (updated)
```

## Error Scenarios

**Backend not responding:**
```
Error: Cannot fetch Swagger from http://localhost:8081/v3/api-docs
Solution: Start backend services with 'docker-compose up backend' or 'mvn spring-boot:run'
```

**Level 1 failed:**
```
⚠️ Level 1 tests failed. Skipping scenario update.
Fix failing tests first: /run-level1-tests
```

**Invalid Gherkin syntax:**
```
Error: Invalid syntax in journeys/features/broken.feature: line 12
Solution: Fix Gherkin syntax before updating scenarios
```

## Integration

**Связанные компоненты:**
- **State ledger:** `.omo/state/testing-assignment.json`
- **Сценарии:** `journeys/features/*.feature`
- **Backend Swagger:** `http://localhost:{8081-8084}/v3/api-docs`
- **Evidence:** `.omo/evidence/task-11-testing-assignment/`

**Conditional routing:**
- **Level 1 failed → SKIP** обновление сценариев
- **Level 1 passed → CONTINUE** синхронизация
- **Level 2 не запускается** пока Level 1 не "passed"

## Quick Start

```bash
# 1. Убедись, что backend запущен
curl http://localhost:8081/v3/api-docs

# 2. Проверь state ledger
cat .omo/state/testing-assignment.json

# 3. Запусти синхронизацию
/update-scenarios

# 4. Проверь изменения
git diff journeys/features/

# 5. Запусти Level 2
/run-level2-journeys
```