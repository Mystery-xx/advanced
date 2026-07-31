# Baseline Evaluation — Ollama Local Model (Zero-Shot)

## Описание

Замер baseline метрик локальной модели через Ollama на eval выборке без fine-tuning (zero-shot inference).

## Модель

- **Модель**: qwen3:14b (по умолчанию)
- **Провайдер**: Ollama (локальный)
- **API**: HTTP `http://localhost:11434`
- **Temperature**: 0.0 (детерминированный режим)
- **Системный промпт**: стандартный промпт классификатора из датасета

```
Ты — классификатор тональности отзывов. Определи категорию отзыва.
Категории: крайне негативный, негативный, нейтральный, позитивный.
Отвечай только названием категории.
```

## Датасет

- **Файл**: `../dataset/eval.jsonl`
- **Примеров**: 20
- **Распределение**: 4 категории (баланс по ~5 на категорию)

## Метрики

| Метрика | Описание |
|---------|----------|
| **Accuracy** | Общая точность классификации |
| **Precision** | Точность по классу |
| **Recall** | Полнота по классу |
| **F1** | F1-мера по классу |
| **Macro-avg** | Среднее арифметическое метрик (без учёта дисбаланса) |
| **Weighted-avg** | Взвешенное среднее (с учётом размера класса) |
| **Confusion Matrix** | Матрица ошибок 4×4 |

## Запуск

### Требования

- Python >= 3.10
- `uv` пакетный менеджер
- **Ollama** установлен и запущен (`ollama serve`)
- **Модель** загружена в Ollama

### Подготовка

```bash
# 1. Запустить Ollama (если ещё не запущен)
ollama serve

# 2. Загрузить модель (если ещё не загружена)
ollama pull qwen3:14b

# Проверить доступные модели
ollama list
```

### Команда

```bash
cd test-project/finetune/baseline

# Базовый запуск (qwen3:14b)
uv run run_baseline.py

# С кастомным путём к eval файлу
uv run run_baseline.py --eval-path /path/to/eval.jsonl

# С другой моделью
uv run run_baseline.py --model llama3.1
```

## Результаты

Результаты сохраняются в `baseline_results.json`:

```json
{
  "model": "qwen3:14b",
  "provider": "ollama",
  "ollama_url": "http://localhost:11434",
  "dataset_path": "test-project/finetune/dataset/eval.jsonl",
  "total_samples": 20,
  "accuracy": 0.85,
  "per_class": {
    "крайне негативный": {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 5},
    ...
  },
  "macro_avg": {"precision": ..., "recall": ..., "f1": ..., "support": 20},
  "weighted_avg": {"precision": ..., "recall": ..., "f1": ..., "support": 20},
  "confusion_matrix": [[...]],
  "classification_report": "...",
  "predictions": [
    {"index": 0, "user_content": "...", "predicted": "...", "actual": "...", "correct": true},
    ...
  ]
}
```

## Используемые библиотеки

| Библиотека | Назначение |
|-----------|-----------|
| `scikit-learn` | Расчёт метрик |
| `rich` | Красивый вывод в терминал |
| `requests` | HTTP-клиент для Ollama API |

## Интерпретация результатов

Этот baseline показывает производительность zero-shot локальной модели. Любой fine-tuned модель следует сравнивать с этими результатами — улучшение по F1 подтверждает эффективность fine-tuning.
