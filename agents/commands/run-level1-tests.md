---
description: Запуск Level 1 тестов (unit + integration) через subagent test-runner
agent: test-runner
---

**Запрос пользователя**: $ARGUMENTS

**Триггер**: Пользователь просит запустить Level 1 тесты, покрыть тестами сервисы, или "протестировать backend".

## Инструкция

### 1. ПЕРЕД запуском
- Убедись, что backend скомпилирован: `cd test-project/backend && mvn clean compile`
- Проверь, что pom.xml содержит зависимости для тестирования (JUnit 5, Mockito, Allure)

### 2. ЗАПУСК
Вызови subagent `test-runner` с контекстом:
```
Источник: test-project/backend/
Модули: user-service, order-service, weather-mcp-service, payment-service
Задача: Покрыть тестами и запустить Level 1 тесты
```

### 3. ОЖИДАЙ результат
Subagent вернёт:
- BUILD status (SUCCESS/FAILED)
- Количество пройденных тестов
- Allure отчёт в `target/allure-results/`
- Coverage отчёт в `coverage-report/`

### 4. ЕСЛИ FAILED
- Читай отчёт subagent'а
- Предложи пользователю:
  - Запустить повторно (если flaky test)
  - Исправить код (если баг)
  - Исправить тест (если ошибка в тесте)

### 5. ОТЧЁТ пользователю
```
Level 1 тесты завершены:
- BUILD: SUCCESS
- Тестов: 48/48
- Покрытие: 72%
- Allure: target/allure-results/

Следующий шаг: Level 2 (E2E) или Level 3 (нагрузочные)
```

## Запрещено
- НЕ запускай тесты без понимания структуры проекта
- НЕ игнорируй failing тесты
- НЕ переходи к Level 2/3 пока Level 1 не зелёный