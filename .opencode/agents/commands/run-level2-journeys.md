# Command: run-level2-journeys

## Trigger

**Команда:** `/run-level2-journeys`

**Описание:** Запуск Level 2 UI-тестирования с использованием subagent `ui-tester` и Playwright MCP.

## Usage

```bash
# Запуск всех сценариев
/run-level2-journeys

# Запуск конкретного сценария
/run-level2-journeys --feature=login.feature

# Запуск с кастомным URL frontend
/run-level2-journeys --url=http://localhost:3001
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

## Execution Flow

1. **Pre-flight checks:**
   - Проверка доступности frontend (`curl localhost:3000`)
   - Проверка Playwright MCP (версия сервера)
   - Валидация `.feature` файлов

2. **Запуск subagent:**
   ```
   subagent: ui-tester
   input: journeys/features/*.feature + localhost:3000
   output: playwright-report/ + screenshots/ + summary.html
   ```

3. **Мониторинг:**
   - Отслеживание прогресса выполнения
   - Логирование ошибок с retry-попытками

4. **Post-processing:**
   - Генерация сводного отчёта
   - Архивация скриншотов
   - Вывод результатов в консоль

## Output

**Артефакты после выполнения:**

```
.omо/evidence/task-5-testing-assignment/
├── playwright-report/
│   └── index.html          # Playwright HTML report
├── screenshots/
│   ├── step-01-*.png       # Скриншоты шагов
│   └── ...
└── summary.html            # Сводный отчёт
```

**Консольный вывод:**
```
✓ Scenario: User login with valid credentials
  ✓ Step 1: Navigate to login page
  ✓ Step 2: Fill email field
  ✓ Step 3: Fill password field
  ✓ Step 4: Click login button
  ✓ Step 5: Verify dashboard visible

✗ Scenario: Admin role navigation
  ✓ Step 1: Navigate to login page
  ✗ Step 2: Fill email field (retry: 2/2)
  ...

Report: .omo/evidence/task-5-testing-assignment/summary.html
```

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
- **Subagent:** `ui-tester` (`.opencode/agents/subagents/ui-tester.md`)
- **MCP Config:** `.opencode/mcp.json` (сервер `playwright`)
- **Сценарии:** `journeys/features/*.feature`
- **Evidence:** `.omo/evidence/task-5-testing-assignment/`

**Следующий шаг:** Task 11 (integration) — автоматизация запуска через CI/CD

## Quick Start

```bash
# 1. Запустить frontend
cd test-project/frontend && npm run dev

# 2. Запустить тесты
/run-level2-journeys

# 3. Открыть отчёт
xdg-open .omo/evidence/task-5-testing-assignment/summary.html
```