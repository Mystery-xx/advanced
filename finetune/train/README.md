# Fine-tuning через Ollama

Скрипт fine-tuning локальной LLM через Ollama API.

## Режимы работы

| Ollama версия | Endpoint | Режим | Изменение весов |
|---|---|---|---|
| >= 0.9.x | `/api/train` | Нейтив | Да |
| < 0.9.x | `/api/create` | few-shot | Нет |

**Текущий Ollama:** 0.31.1 — используется `/api/create`.

## Что делает скрипт

1. **Проверка** — Ollama запущен, модель доступна, датасет валиден
2. **Конвертация** — train.jsonl → Ollama Modelfile формат
3. **Создание модели** — few-shot примеры в system prompt
4. **Оценка** — quick eval на eval.jsonl

## Запуск

```bash
cd test-project/finetune/train

# Базовый запуск
uv run finetune.py

# С кастомными параметрами
uv run finetune.py --model qwen3:14b --tag my-model
uv run finetune.py --train-path custom/train.jsonl --skip-eval

# Только конвертация (без создания модели)
uv run finetune.py --skip-eval --tag dry-run
```

## Параметры

| Флаг | По умолчанию | Описание |
|---|---|---|
| `--model` | `qwen3:14b` | Базовая модель |
| `--tag` | `qwen3:14b-sentiment` | Тег итоговой модели |
| `--train-path` | `../dataset/train.jsonl` | Путь к train датасету |
| `--eval-path` | `../dataset/eval.jsonl` | Путь к eval датасету |
| `--epochs` | `3` | Для `/api/train` |
| `--learning-rate` | `5e-5` | Для `/api/train` |
| `--batch-size` | `4` | Для `/api/train` |
| `--skip-eval` | `false` | Пропустить оценку |

## Выходные файлы

| Файл | Описание |
|---|---|
| `train_ollama.jsonl` | Конвертированный датасет |
| `Modelfile` | Modelfile для `/api/create` |
| `training_results.json` | Результат обучения |

## Модели

```bash
ollama list
# qwen3:14b-sentiment

# Запуск модели
ollama run qwen3:14b-sentiment

# Удаление
ollama rm qwen3:14b-sentiment
```

## Использование модели

```python
import requests

resp = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen3:14b-sentiment",
        "messages": [
            {"role": "system", "content": (
                "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
                "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
                "Отвечай только названием категории."
            )},
            {"role": "user", "content": "Отзыв о товаре"},
        ],
        "temperature": 0.0,
        "stream": False,
    },
)
print(resp.json()["message"]["content"])
```

> **Важно:** Modelfile system prompt — это hint. Явный system message в chat
> запросе перекрывает его. Всегда передавайте system prompt в request.

## Сравнение с baseline

```bash
# Baseline (zero-shot)
cd ../baseline && uv run run_baseline.py --model qwen3:14b

# После fine-tuning
uv run run_baseline.py --model qwen3:14b-sentiment
```

## Для Ollama 0.9.x+ с /api/train

На новых версиях Ollama доступен полноценный fine-tuning:

```bash
ollama train my-model -f train_ollama.jsonl --epochs 3 --learning-rate 0.00005
```

Скрипт автоматически определяет доступность `/api/train` и использует
правильный режим.
