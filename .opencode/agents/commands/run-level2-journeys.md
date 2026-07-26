# Command: run-level2-journeys

## Trigger

**Команда:** `/run-level2-journeys`

**Описание:** Запуск Level 2 UI-тестирования с использованием Playwright MCP — выполняет тесты напрямую.

**Делегируй через `task(subagent_type="ui-tester", ...)` — не выполняй тесты напрямую.**

## Usage

```bash
# Запуск всех сценариев
/run-level2-journeys

# Запуск конкретного сценария
/run-level2-journeys --feature=login.feature

# Запуск с кастомным URL frontend
/run-level2-journeys --url=http://localhost:3001
```

## Delegation Pattern

**Эта команда — обёртка для сабагента `ui-tester`.**

### Execution Flow

1. **Parse arguments** from `$ARGUMENTS`:
   - Feature file: `login.feature` (default: "all")
   - Frontend URL: `--url=http://localhost:3001` (default: "http://localhost:3000")

2. **Delegate to subagent** via `task()`:
```typescript
task(subagent_type="ui-tester", {
  feature: "<parsed-feature-or-all>",
  url: "<parsed-url-or-default>"
})
```

3. **Forward result** to user:
   - Scenario execution results (per step)
   - HTML report path
   - Screenshot locations
   - summary.html path

### Usage

```bash
/run-level2-journeys                           # Все .feature файлы
/run-level2-journeys --feature=.feature   # Только login.feature
/run-level2-journeys --url=http://localhost:3001  # Кастомный URL
```

## Prerequisites

**Перед запуском убедись:**

1. **Frontend запущен:**
   ```bash
   cd test-project/frontend
   npm run dev
   # или
   docker-compose up frontend
   ```

2. **Playwright MCP настроен:**
   - Файл `.opencode/mcp.json` существует
   - Сервер `playwright` включён (`enabled: true`)

3. **Сценарии готовы:**
   - Файлы `journeys/features/*.feature` существуют
   - Синтаксис Gherkin валиден

## Execution

Эта команда делегирует работу сабагенту `ui-tester`. Не выполняй тесты напрямую.

1. Извлеки аргументы из `$ARGUMENTS`
2. Вызови `task(subagent_type="ui-tester", params)`
3. Дождись результата от сабагента
4. Передай отчёт пользователю в формате:
```
✓ Scenario: User login with valid credentials
  ✓ Step 1: Navigate to login page
  ✓ Step 2: Fill email field
  ...

Report: .omo/evidence/task-5-testing-assignment/summary.html
```

## Ограничения:
- НЕ пропускай шаги сценариев
- НЕ игнорируй failing тесты
- НЕ делай скриншоты без явного шага в сценарии

## Error Scenarios

**Frontend not responding:**
```
Error: Frontend not available at http://localhost:3000
Solution: Start frontend with 'npm run dev' or 'docker-compose up frontend'
```

**Playwright MCP not connected:**
```
Error: Playwright MCP server not available on port 8931
Solution: Check .opencode/mcp.json and restart MCP server
```

**Invalid feature file:**
```
Error: Invalid Gherkin syntax in journeys/features/broken.feature: line 12
Solution: Fix syntax error before running tests
```

## Integration

**Связанные компоненты:**
- **MCP Config:** `.opencode/mcp.json` (сервер `playwright`)
- **Сценарии:** `journeys/features/*.feature`
- **Evidence:** `.omo/evidence/task-5-testing-assignment/`

**Следующий шаг:** Task 11 (integration) — автоматизация запуска через CI/CD

## Quick Start

```bash
# 1. Запустить frontend
cd test-project/frontend && npm run dev

# 2. Запустить тесты (команда делегирует сабагенту ui-tester)
/run-level2-journeys

# 3. Открыть отчёт
xdg-open .omo/evidence/task-5-testing-assignment/summary.html
```