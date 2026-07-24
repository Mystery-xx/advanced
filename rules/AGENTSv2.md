# AGENTS.md — Leroy Merlin Russia PlatformECO BFF Autotests

**Project Type**: Kotlin/Cucumber BDD API Test Framework (Test-Only, Zero Production Code)  
**Domain**: BFF (Backend-For-Frontend) Definitions Validation  
**Stack**: Kotlin 1.9+, Maven Multi-Module, Cucumber JVM, TestNG, WireMock, Redis, Docker  
**Core Dependency**: `autotests-core v2.5.5` (external shared library)

---

## 📋 О проекте

Фреймворк API-тестирования BFF-дефиниций на Kotlin + Cucumber.

**Стек:** Kotlin 1.9, Maven, Cucumber 6, RestAssured, AssertJ, JsonUnit, Allure, WireMock, TestNG

**Модули:**
- `pao/` — заказы, услуги
- `ucc/` — Checkout, корзина
- `payment/` — платежи
- `shoppinglist/` — список покупок
- `omnicart/` — omnichannel корзина

---

## 🏗️ Архитектура и Мокирование

### Request Flow

```
Автотесты (Kotlin/Cucumber) → BFF (Backend-For-Frontend) → Backend Services
```

**Как работает:**
1. **Автотесты отправляют HTTP-запросы к BFF** — тесты работают на уровне API, вызывая эндпоинты BFF напрямую
2. **BFF отправляет запросы к Backend Services** — BFF выступает как middleware, передающий запросы дальше (cart service, checkout service, и т.д.)
3. **Автотесты мокируют Backend** — чтобы тесты были стабильными и изолированными, вызовы от BFF к Backend мокируются через WireMock

### ⚠️ КРИТИЧНО: ДВЕ таблицы в feature-файлах

**Backend Stub Matrix** (в шаге `Дано инициализировать заглушки для ветки`):
- Определяет, что **Backend возвращает BFF** (INPUT)
- **НЕ МЕНЯТЬ** для задач про ответы BFF

**Examples Table**:
- Определяет, что **BFF возвращает фронтенду** (OUTPUT)
- **МЕНЯТЬ** для задач про ответы BFF

**Пример из PAO-10570:**
- Задача: изменить ответ BFF 503→500 при ошибках бекенда
- ❌ ОШИБКА: менять Backend Stub Matrix (строка `| Solution get | ... | 503_error |`)
- ✅ ПРАВИЛЬНО: менять только Examples Table (statusCode в ответе BFF)

---

## 🎯 Flow (Task States)

### Анализ задачи (ПЕРЕД началом работы)

**Обязательные источники для изучения:**

1. **Сама задача** — описание, требования, критерии приемки
2. **Родительская задача** — контекст, общая цель эпика
3. **Связанные задачи** — блокирующие, зависимые, дубликаты
4. **Документация** — Yandex Wiki, спецификации API, дизайн-документы
5. **Комментарии** — обсуждения, уточнения требований

**Игнорировать:**
- ❌ **PR (Pull Requests)** — приложенные к задачам PR не изучать (могут быть тестовыми, устаревшими, невалидными)

**Workflow:**
```
1. Прочитать задачу → 2. Найти родительскую → 3. Изучить связанные
→ 4. Проверить Wiki → 5. Игнорировать PR → 6. Начать анализ кода
```

**Yandex Wiki интеграция:**
- Использовать `yandex-wiki_page_get` для получения документации
- Искать по slug: `pao/{task-number}` или `bff/{component}`
- Проверять вложенные страницы через `yandex-wiki_page_get_descendants`

### Обязательная загрузка скиллов

**ПЕРЕД работой с feature-файлами:**
```
skill(name="cucumber-gherkin")
```

**Когда загружать:**
- ✏️ Редактирование `.feature` файлов
- ✏️ Написание step definitions
- ✏️ Добавление Examples таблиц
- ✏️ Работа с Gherkin-синтаксисом

**Почему:** Скилл содержит актуальные правила синтаксиса Gherkin, паттерны step definitions, hooks, и best practices для BDD тестирования.

Следовать строгому порядку:

1. **RESEARCH** — Изучить существующие тесты, найти примеры в проекте
2. **PLAN** — Спроектировать структуру, определить необходимые моки
3. **EXECUTE** — Написать заглушки → код шагов → feature-файл
4. **VALIDATION** — Запустить тесты (`mvn test`), проверить Allure

Не переходить к следующей стадии без завершения текущей.

---

## 📋 Правила таблиц в feature-файлах

**ОБЯЗАТЕЛЬНО**:

1. **ЗАГРУЗИ SKILL `cucumber-gherkin`** перед редактированием feature-файлов
2. Колонка `description` в конце каждой таблицы Примеры
3. Выравнивание колонок по самому длинному значению
4. Формат: `| value |` (один пробел вокруг значения)
5. 6-пробельная индентация внутри сценариев
6. Границы колонок на одной вертикальной линии

**Пример с длинными значениями**:
```gherkin
# ✅ ПРАВИЛЬНО — все | на одной вертикали
Примеры:
  | header            | value      | message                                                                            |
  | front-application | MagPortal1 | headers/front-application must match pattern "^(MagPortal\|MagMobile)$"            |
  | channel           | OFFLINE2   | headers/channel must match pattern "^(OFFLINE\|ONLINE\|CC)$"                       |
  | device-type       | 6          | headers/device-type must match pattern "^(0\|1\|2\|3\|4\|5)$"                      |

# ❌ НЕПРАВИЛЬНО — границы не выровнены
Примеры:
  | header | value | message |
  | front-application | MagPortal1 | headers/front-application must match pattern "^(MagPortal\|MagMobile)$" |
  | channel | OFFLINE2 | headers/channel must match pattern "^(OFFLINE\|ONLINE\|CC)$" |
```

**Правила**:
- Каждая колонка выравнивается по самому длинному значению в ней
- Короткие значения дополняются пробелами
- Длинные значения в одной колонке НЕ влияют на ширину других
- Вертикальные границы `|` должны быть на одной линии
- **АЛГОРИТМ**: (1) Найди самое длинное значение в колонке → (2) Добавь 2 пробела (по 1 с каждой стороны) → (3) Все ячейки дополни пробелами до этой ширины
- **Пример**: Если макс. значение = 72 символа → все ячейки = 74 символа (`| value |`)
- **⚠️ КРИТИЧНО:** Header и data rows выравниваются ПО ОБЩЕМУ МАКСИМУМУ — НЕ форматируй header отдельно от данных!
- **⚠️ ВАЖНО:** Таблицы могут содержать закомментированные строки (`# ...`) — НЕ удаляй их, это документация!
- **⚠️ НЕ создавай дубликаты строк** — скрипт `validate_tables.py --fix` может дублировать строки branch8, branch9 при наличии комментариев в таблице. Проверяй результат вручную!
- **⚠️ КРИТИЧНО:** Символы `\|` внутри regex-паттернов (например, `"^(A\|B\|C)$"`) — это НЕ разделители колонок! Это экранированные символы внутри строкового значения.
- **⚠️ ЗАПРЕЩЕНО:** Автоматическое форматирование таблиц скриптами без предварительного экранирования `\|` → placeholder → обработка → восстановление. Только ручное форматирование или скрипт с правильной обработкой `\|`.
- **⚠️ ТАБЛИЦЫ С КОММЕНТАРИЯМИ:** Если таблица содержит закомментированные строки (`# | ... |`) внутри, ВСЕ активные строки (до и после комментариев) выравниваются как единая таблица. Закомментированные строки НЕ влияют на ширину колонок — активные строки выравниваются по самому длинному значению среди ВСЕХ активных строк.
- **⚠️ ТАБЛИЦА С ОДНОЙ СТРОКОЙ:** Если в таблице только одна активная строка (например, хэдер), правило 1 пробела ВСЁ РАВНО должно соблюдаться: `| value |` (один пробел до и после значения).

### 🔧 Скрипт проверки таблиц

Используй этот скрипт для проверки всех feature-файлов перед коммитом:

```bash
# Режим валидации (только проверка)
python3 scripts/validate_tables.py

# Режим авто-фикса (исправляет ошибки форматирования)
python3 scripts/validate_tables.py --fix

# Проверка конкретных файлов
python3 scripts/validate_tables.py path/to/file1.feature path/to/file2.feature
```

**Режимы работы**:
- **Без флагов**: Валидация — проверяет все таблицы, сообщает об ошибках
- **`--fix`**: Авто-фикс — выравнивает все таблицы по правилу 1-space padding

**Что проверяет**:
- ✅ Все таблицы после `Примеры:` / `Examples:`
- ✅ Выравнивание `|` по вертикали (одинаковые позиции во всех строках)
- ✅ Корректную обработку `\|` в regex (не считает их разделителями колонок)
- ✅ Таблицы с закомментированными строками

**Что НЕ проверяет** (требует ручной проверки):
- ❌ Наличие колонки `description` в Examples
- ❌ Осмысленность значений в `description`
- ❌ Интерполяцию `<description>` в названии сценария
- ❌ Правило 1-space padding (проверяет только выравнивание `|`)

---

## ❌ Инварианты (НЕЛЬЗЯ)

- Писать тесты беков нижележащих сервисов
- Использовать `any` Kotlin
- Делать `println` в коде шагов
- Хардкодить значения (использовать переменные `${orderId}`)
- Оставлять пустые catch-блоки
- Писать монолитные сценарии без `Scenario Outline`
- Писать заглушки без валидации входящих параметров (`bodyPatterns`, `queryParameters`)
- Указывать путь к моку с расширением `.json` (только без расширения!)
- Забывать проверять `.gitignore` перед коммитом
- **Менять файлы без проверки тегов** (сначала `grep -r "@united_middle"`)
- **Удалять колонку `description`** из таблиц Examples
- **Криво форматировать таблицы** (выравнивай колонки!)
- **Ломать таблицы с `\|` в regex** (это не разделители колонок!)
- **Автоматически форматировать таблицы без обработки `\|`** (сначала `\|` → placeholder → форматирование → восстановление)
- **Ломать форматирование таблиц с закомментированными строками** (активные строки ДО и ПОСЛЕ комментариев выравниваются как единая таблица — закомментированные строки НЕ влияют на ширину колонок)
- **Нарушать правило 1 пробела в таблицах с одной строкой** (даже если строка только одна, должно быть `| value |`)

---

## 📐 Naming Conventions

| Тип      | Формат                        | Пример                      |
| -------- | ----------------------------- | --------------------------- |
| Feature  | `{entity}_{action}.feature`     | `get_checkouts.feature`       |
| Заглушки | `{name}_{status}_{suffix}.json` | `crt_in_3_get_200.json`, `post_order_200_3services.json` |
| Response | `{entity}_{action}_{scenario}.json` | `order_post_ok.json` |
| Steps    | `{Module}Steps.kt`              | `UccSteps.kt`                 |
| Теги     | `@{entity}_{version}`           | `@carts_v3`                   |

---

## 📁 Структура модуля

```
{module}/src/test/
├── kotlin/ru/leroymerlin/qa/
│   ├── steps/{Module}Steps.kt
│   └── redis/RedisService.kt
└── resources/
    ├── features/       # .feature
    ├── mocks/          # заглушки WireMock
    ├── requests/       # шаблоны запросов
    └── responses/      # эталоны для сравнения
```

### Структура mocks (иерархия)

```
mocks/
└── функционал (cart, checkout)/
    └── ручка (get_cart_v3)/
        └── сервис (crt_in3_get, rms, storerepository)/
            ├── заглушка_200.json
            ├── заглушка_400.json
            └── заглушка_500.json
```

---

## 🧩 Примеры правильного кода

### Заглушка WireMock с валидацией bodyPatterns

```json
{
  "request": {
    "method": "POST",
    "url": "/prices/rms/prices/v2/recommended-prices",
    "bodyPatterns": [
      {
        "equalToJson": {
          "itemId": [81963491],
          "locationId": [35],
          "offset": 0,
          "limit": 10
        }
      }
    ]
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "jsonBody": { "cartId": "123" }
  }
}
```

### Заглушка с валидацией queryParameters и headers

```json
{
  "request": {
    "method": "POST",
    "url": "/checkout-v2/api/v1/cart",
    "headers": {
      "Authorization": { "equalTo": "Bearer eyJhbGciO" }
    },
    "queryParameters": {
      "orderId": {
        "or": [
          { "equalTo": "INVALID" },
          { "equalTo": "572cdcc-741d-4b33-a639-237afdf24add" }
        ]
      }
    }
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "jsonBody": { "cartId": "123" }
  }
}
```

### Kotlin-шаг с DI и TestContext

```kotlin
class UccSteps @Inject constructor(private val serviceProvider: ServiceProvider) {
    private val redisService by lazy { RedisService() }

    @Inject
    lateinit var testContext: TestContext

    @И("тело ответа соответствует json-файлу {string}")
    fun responseBodyEqualTo(expectedJson: String) {
        assertThatJson(testContext.response!!.body.asPrettyString())
            .`when`(Option.IGNORING_ARRAY_ORDER)
            .isEqualTo("responses/${expectedJson}.json".resourceToString())
    }

    @И("очистить redis")
    fun clearRedisCache() {
        redisService.clearRedisCache()
    }

    @И("добавить данные в redis: key {string} value {string}")
    fun addDataToRedis(key: String, value: String) {
        redisService.addData(key, value)
    }
}
```

### Feature-файл с тремя типами сценариев

```gherkin
#language: ru
@orders @v3
Функция: Создание заказа POST /v3/orders

  Предыстория:
    * маппинг заглушек
      | get-cart | mocks/order/post/get_cart/crt_in_3_get  |
      | orderv2  | mocks/order/post/ord2/post     |
    * добавить хедеры
      | shopid   | 35       |
      | ldap     | 60095859 |

  # Тип 1: Ошибки данных
  Структура сценария: Проверка обязательных хедеров
    * удалить хедер "<headerName>"
    * отправить POST запрос на адрес "/v3/orders"
    * возвращается статус код <statusCode>
    * тело error ответа содержит message "<message>"

    Примеры:
      | headerName | message                                        | statusCode |
      | shopid     | headers should have required property 'shopid' | 400        |
      | ldap       | headers should have required property 'ldap'   | 400        |

  # Тип 2: Ошибки сервисов
  Структура сценария: Проверка ошибок сервисов бекенда
    Дано инициализировать заглушки для ветки "<branch>"
      | node     | branch1 | branch2 |
      | get-cart | 400     | 500     |
      | orderv2  | -       | -       |
    * отправить POST запрос на адрес "/v3/orders"
    * возвращается статус код <statusCode>
    * тело error ответа содержит code <code> и message "<message>"

    Примеры:
      | branch  | statusCode | code | message                         |
      | branch1 | 503        | 175  | General cart error: Bad Request |
      | branch2 | 503        | 175  | General cart error: Internal Error |

  # Тип 3: Позитивные сценарии
  Структура сценария: Позитивные сценарии. <description>
    Дано инициализировать заглушки для ветки "<branch>"
      | node     | branch1 |
      | get-cart | 200     |
      | orderv2  | 200     |
    * подготавливаем тело запроса на основе json-файла "order/post/payload"
    * отправить POST запрос на адрес "/v3/orders"
    * возвращается статус код 200
    * тело ответа соответствует содержимому json-файла "order/post/ok"

    Примеры:
      | branch  | description              |
      | branch1 | 1 продукт с услугой      |
```

### Работа с Redis (для ucc, omnicart)

```kotlin
private val redisService by lazy { RedisService() }

@И("добавить данные в redis: key {string} value {string}")
fun addDataToRedis(key: String, value: String) {
    redisService.addData(key, value)
}
```

---

## 🔑 Ключевые концепции

### TestContext

Объект, живущий в рамках одного теста:

| Свойство     | Описание                    |
| ------------ | --------------------------- |
| `request`    | Последний отправленный запрос |
| `response`   | Последний полученный ответ   |
| `statusCode` | Статус-код последнего ответа |
| `payload`    | Тело последнего запроса      |
| `variables`  | Словарь переменных сценария  |

**Пример использования переменной:**
```gherkin
* отправить DELETE запрос на адрес "/v3/carts/${cartId}/items"
```

### Ветки (Branches) в Scenario Outline

```gherkin
Дано инициализировать заглушки для ветки "<branch>"
  | node     | branch1 | branch2 |
  | get-cart | 400     | 500     |
  | orderv2  | -       | -       |
```

- Сценарий выполнится столько раз, сколько столбцов с ветками
- Значение `400`, `500` — суффикс в имени файла заглушки
- `-` означает заглушку по умолчанию из маппинга

### Маппинг заглушек

```gherkin
* маппинг заглушек
  | get-cart            | mocks/cart/get_cart_v3/crt_in3_get/crt_in_3_get      |
  | store-repository-id | mocks/cart/get_cart_v3/storerepository/store_repo_id |
```

**Важно:** Путь указывается **без расширения `.json`**!

---

## 🚀 Быстрый старт

1. `mvn compile -U` — скачать зависимости
2. `cd pao && mvn test` — запустить тесты модуля
3. `allure serve target/allure-results` — открыть отчёт

---

## 🚀 Команды

```bash
mvn test                                    # Все тесты
cd pao && mvn test                          # Конкретный модуль
mvn test -Dcucumber.filter.tags="@test"     # По тегу
allure serve target/allure-results          # Отчёт
allure open target/allure-results           # Открыть в браузере

# Проверка scope изменений
grep -r "@united_middle" --include="*.feature" -   # Все файлы единого BFF
grep -r "@mobile_bff" --include="*.feature" -l      # Мобильный BFF
```

---

## 💬 Профиль взаимодействия

- **Язык:** Русский (общение, feature-файлы), Английский (код)
- **Стиль:** Лаконичный, технический
- **Приоритет:** Сначала исследовать существующие паттерны в проекте
- **Документация:** README.md — авторитетный источник архитектуры

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

**⚠️ Терминология (КРИТИЧНО):**
- **"BFF Checkout"** = весь `@united_middle` (checkouts/, carts/, cma/, services/, kz/, typ/)
- **"Мобильный BFF"** = `@mobile_bff`, `@bff_mobile` (только mobile/)
- **"Checkout" (без "BFF")** = только `checkouts/` модуль

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

**MANDATORY workflow for task-based changes:**

```bash
# 1. ALWAYS check which files have the relevant tag BEFORE making changes
grep -r "@united_middle" --include="*.feature" -l
grep -r "@mobile_bff" --include="*.feature" -l

# 2. Verify with user if scope is unclear

# 3. NEVER assume scope based on "BFF" keyword alone
# Different modules = different BFF services
```

**Common Mistake to Avoid:**
> ❌ "Задача про BFF → меняю только checkouts/"  
> ✅ "Задача про BFF → проверяю тег `@united_middle` → меняю ВСЕ модули с этим тегом (checkouts/, carts/, cma/, services/, kz/, typ/)"

**MANDATORY: Уточнение scope ПЕРЕД изменениями**

1. **Проверить теги grep-ом** — найти ВСЕ файлы с релевантным тегом:
   ```bash
   grep -r "@united_middle" --include="*.feature" -l
   grep -r "@mobile_bff" --include="*.feature" -l
   ```

2. **Сверить с задачей** — если задача говорит "Checkout", уточнить:
   - "BFF Checkout" → менять ВСЕ файлы с `@united_middle`
   - "Checkout" (без BFF) → только `checkouts/` модуль?

3. **НЕ менять файлы без тега**:
   - `omnicart/` — тег `@omnicart` (НЕ `@united_middle`)
   - `mobile/` — теги `@mobile_bff`, `@bff_mobile` (НЕ `@united_middle`)
   - `pao/` — может не иметь тега

4. **Спросить при неоднозначности** — НЕ делать предположений о scope

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
- **NEVER** edit `TestRunner.kt` files — they are auto-generated infrastructure
- **NEVER** modify feature files without checking tags first — ALWAYS run `grep -r "@united_middle"` BEFORE changes
- **NEVER** assume scope from "BFF" keyword — "BFF Checkout" = all `@united_middle` modules, not just checkouts/

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