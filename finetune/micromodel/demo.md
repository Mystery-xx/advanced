# Demo: Micro-Model Router

## Предварительные требования

- Ollama запущен: `ollama serve` (в отдельном терминале)
- Модель qwen3:14b скачана: `ollama pull qwen3:14b`

---

## Сценарий демонстрации

### 1. Проверка окружения

```bash
curl -s http://localhost:11434/api/tags | head -c 200 && ollama list | head -5
```

### 2. Тренировка микро-модели (TF-IDF + LogisticRegression на 80 примерах)

```bash
cd /mnt/f/git/advanced/finetune/micromodel && uv run train.py
```

### 3. Оценка на 35 примерах с порогом 0.30 (баланс между скоростью и точностью)

```bash
cd /mnt/f/git/advanced/finetune/micromodel && uv run run_evaluation.py --confidence-threshold 0.30 --output micromodel_results.json
```

### 4. Оценка с повышенным порогом 0.50 или 0.75 (консервативный режим, требует 500+ примеров в тренировке)

```bash
cd /mnt/f/git/advanced/finetune/micromodel && uv run run_evaluation.py --confidence-threshold 0.50 --output micromodel_results_t50.json
```

### 5. Демо на 5 ручных запросах (2 простых + 2 граничных + 1 сложный)

```bash
cd /mnt/f/git/advanced/finetune/micromodel && uv run demo_run.py
```

### 6. Интерактивный запуск роутера с одним запросом через CLI

```bash
cd /mnt/f/git/advanced/finetune/micromodel && python -c "from micromodel_router import MicroModelRouter; r=MicroModelRouter(); print(r.route('Отличный товар, всем советую'))"
```

### 7. Сравнение с baseline (LLM zero-shot)

```bash
cd /mnt/f/git/advanced/finetune/micromodel/../baseline && uv run run_baseline.py 2>/dev/null || echo "Baseline script requires finetune setup"
```

---

## Ожидаемые результаты

| Шаг | Что проверяем | Ожидание |
|-----|---------------|----------|
| 1 | Ollama работает | Json с тегами, список моделей |
| 2 | Тренировка | Accuracy 100%, 3 `.pkl` файла в `models/` |
| 3 | Оценка threshold=0.30 | Fallback ~30-40%, micro-model accuracy ~70-75%, avg latency ~1-5s |
| 4 | Оценка threshold=0.50+ | Fallback ~90-100% (требует 500+ примеров в тренировке) |
| 5 | Demo 5 запросов | Микс: ~60-70% через микро-модель (<1s), ~30-40% через LLM (15-30s) |
| 6 | CLI запрос | RouterResult с полями answer/model/latency |
| 7 | Baseline | Accuracy ~80% (только LLM, без роутинга) |

---

## Структура проекта

```
finetune/micromodel/
├── train.py                # Тренировка
├── micromodel_router.py    # Роутер с fallback
├── run_evaluation.py       # Оценка метрик
├── demo_run.py             # Демо 5 запросов
├── demo.md                 # Этот сценарий
├── README.md               # Полная документация
├── models/*.pkl            # Обученные модели
└── micromodel_results.json # Результаты оценки
```
