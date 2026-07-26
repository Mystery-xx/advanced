---
description: Запуск Level 1 тестов (unit + integration) — делегирует сабагенту test-runner
agent: run-level1-tests
---

**Запрос пользователя**: $ARGUMENTS

**Триггер**: Пользователь просит запустить Level 1 тесты, покрыть тестами сервисы, или "протестировать backend".

## Delegation Pattern

**Эта команда — обёртка для сабагента test-runner.**

### Execution Flow

1. **Parse arguments** from `$ARGUMENTS`:
   - Service name(s): `payment-service`, `user-service`, etc. (default: "all")
   - Flags: `--action=run_only` (optional)

2. **Delegate to subagent** via `task()`:
```typescript
task(subagent_type="test-runner",
  service: "<parsed-service-or>",
  scope: "level1",
  action: "<write_and_run|run_only>"
})
```

3. **Forward result** to user:
   - BUILD status (SUCCESS/FAILED)
   - Test count (X/Y passed)
   - Coverage percentage
   - Allure report path

### Usage

```bash
/run-level1-tests                           # Все 4 сервиса
/run-level1-tests payment-service           # Только payment-service
/run-level1-tests payment-service user-service  # Несколько сервисов
/run-level1-tests --action=run_only payment-service  # Только запуск
```

## Execution

Эта команда делегирует работу сабагенту `test-runner`. Не выполняй тесты напрямую.

1. Извлеки аргументы из `$ARGUMENTS`
2. Вызови `task(subagent_type="test-runner", params)`
3. Дождись результата от сабагента
4. Передай отчёт пользователю в формате:
```
Level 1 тесты завершены:
- BUILD: SUCCESS/FAILED
- Тестов: X/Y
- Покрытие: Z%
- Allure: target/allure-results/
```

## Ограничения:
- НЕ пиши интеграционные тесты (только unit)
- НЕ игнорируй failing тесты
- НЕ переходи к Level 2/3 пока Level 1 не зелёный
- НЕ меняй production код (только тесты)

## Запрещено:
- ❌ Подавлять ошибки в тестах
- ❌ Удалять failing-тесты чтобы "прошли"
- ❌ Запускать тесты без понимания структуры проекта
