# Demo: Model Routing с Confidence-Based Fallback

**Время:** 5-7 минут  
**Цель:** Показать автоматическую эскалацию от дешёвой модели к дорогой при низкой уверенности

---

## 1. Введение (30 сек)

**Конфигурация по умолчанию:**
- **Cheap model:** `llama3.1:8b` (быстрая, 1 cost unit)
- **Expensive model:** `qwen2.5-coder:7b-instruct` (мощная, 3 cost units)
- **Escalation:** MEDIUM + LOW confidence

**Что покажем:**
- Запуск evaluation на датасете
- Метрики: escalation rate, cost savings, latency
- JSON результаты с полной трассировкой

---

## 2. Запуск Evaluation (2 мин)

### Команда (одна строка):
```bash
cd /mnt/f/git/advanced && PYTHONPATH=. uv run finetune/routing/run_routing.py --eval-path finetune/dataset/eval.jsonl
```

### Ожидаемый вывод:
```
═══════════════════════════════════════════════════════
ROUTING EVALUATION SUMMARY
═══════════════════════════════════════════════════════

Routing Statistics:
  Total examples:      20
  Cheap model:         20 (100.0%)
  Expensive model:     0 (0.0%)
  Escalation rate:     0.0%

Latency Statistics:
  Avg latency:         2754 ms
  Min latency:         1823 ms
  Max latency:         4102 ms

Cost Statistics:
  Total cost units:    20
  Avg per request:     1.0
  Cost savings:        66.67% vs all-expensive
═══════════════════════════════════════════════════════

Results saved: routing_results.json
```

### Комментарий:
> "Все 20 запросов получили HIGH confidence от дешёвой модели — эскалация не потребовалась. Экономия 66.67% cost vs запуск всех на дорогой модели."

---

## 3. Проверка JSON Results (1 мин)

### Команда (одна строка):
```bash
cat /mnt/f/git/advanced/finetune/routing/routing_results.json | python3 -m json.tool | head -50
```

### Ожидаемая структура:
```json
{
  "routing_statistics": {
    "total_examples": 20,
    "cheap_model_count": 20,
    "expensive_model_count": 0,
    "escalation_rate": 0.0,
    "cheap_percentage": 100.0,
    "expensive_percentage": 0.0
  },
  "latency_statistics": {
    "avg_latency_ms": 2754.4,
    "min_latency_ms": 1823,
    "max_latency_ms": 4102
  },
  "cost_statistics": {
    "total_cost_units": 20,
    "avg_cost_per_request": 1.0,
    "cost_savings_vs_all_expensive": 66.67
  },
  "predictions": [...]
}
```

---

## 4. Демонстрация кода (2 мин)

### Показать файл: `model_router.py` (строки 150-180)

**Команда (одна строка):**
```bash
sed -n '150,180p' /mnt/f/git/advanced/finetune/routing/model_router.py
```

### Ключевая логика:
```python
def route_request(question: str, config: RouterConfig) -> RouterResult:
    # 1. Запрос к дешёвой модели
    cheap_answer = classify(question, config.cheap_model, config.ollama_url)
    
    # 2. Вычисление confidence (self-check + constraint check)
    confidence_status = compute_confidence(question, cheap_answer.answer, config)
    
    # 3. Эскалация при MEDIUM/LOW
    if confidence_status in config.escalate_on:
        expensive_answer = classify(question, config.expensive_model, ...)
        return RouterResult(..., escalated=True, ...)
    
    return RouterResult(..., escalated=False, ...)
```

### Комментарий:
> "Если cheap модель даёт MEDIUM или LOW confidence — система автоматически переключается на expensive модель."

---

## 5. Симуляция Low Confidence (1 мин)

### Сценарий:
```
Вопрос: "Объясни квантовую запутанность"
→ llama3.1:8b отвечает → self-check даёт LOW confidence
→ Эскалация на qwen2.5-coder:7b-instruct
→ Возвращаем ответ qwen3 + флаг escalated=True
```

### Тест на сложных вопросах (будущее):
**Команда (одна строка):**
```bash
uv run run_routing.py --eval-path finetune/dataset/hard_questions.jsonl --escalate-on LOW
```

**Ожидаемый результат:**
- Escalation rate: 30-50%
- Cost savings: 40-60%
- Higher accuracy на сложных вопросах

---

## 6. Дополнительные команды для демо

### Запуск с кастомными моделями (одна строка):
```bash
uv run run_routing.py --eval-path ../dataset/eval.jsonl --cheap-model llama3.1:8b --expensive-model qwen2.5-coder:7b-instruct --escalate-on MEDIUM LOW
```

### Запуск с сохранением в кастомный путь (одна строка):
```bash
uv run run_routing.py --eval-path ../dataset/eval.jsonl --output /tmp/routing_demo_results.json
```

### Проверка количества эскалаций (одна строка):
```bash
cat routing_results.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"Escalated: {d['routing_statistics']['expensive_model_count']}/{d['routing_statistics']['total_examples']}\")"
```

### Проверка cost savings (одна строка):
```bash
cat routing_results.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"Cost savings: {d['cost_statistics']['cost_savings_vs_all_expensive']:.2f}%\")"
```

---

## 7. Итоги (30 сек)

### Преимущества:
| Метрика | Значение | Интерпретация |
|---------|----------|---------------|
| **Escalation rate** | 0-50% | % запросов на дорогой модели |
| **Cost savings** | 30-70% | Экономия vs single expensive model |
| **Avg latency** | 1-5 sec | Среднее время ответа |
| **Cheap model accuracy** | 70-90% | Точность на простых вопросах |

### Ключевые выводы:
- ✅ **66% экономии** на простых запросах
- ✅ **Автоматическая эскалация** на сложных
- ✅ **Полная трассировка**: какой моделью отвечен каждый запрос
- ✅ **Гибкая настройка**: пороги confidence, модели, cost ratio

### Следующие шаги:
- Тестирование на production-подобных вопросах
- Настройка порогов escalation под use case
- A/B тест: routing vs single model

---

## Quick Reference: Все команды в одном месте

```bash
# 1. Запуск evaluation (из корня проекта с PYTHONPATH)
cd /mnt/f/git/advanced && PYTHONPATH=. uv run finetune/routing/run_routing.py --eval-path finetune/dataset/eval.jsonl

# 2. Проверка JSON
cat finetune/routing/routing_results.json | python3 -m json.tool | head -50

# 3. Показать код routing
sed -n '150,180p' finetune/routing/model_router.py

# 4. Кастомные модели
cd /mnt/f/git/advanced && PYTHONPATH=. uv run finetune/routing/run_routing.py --eval-path finetune/dataset/eval.jsonl --cheap-model llama3.1:8b --expensive-model qwen2.5-coder:7b-instruct --escalate-on MEDIUM LOW

# 5. Кастомный output
cd /mnt/f/git/advanced && PYTHONPATH=. uv run finetune/routing/run_routing.py --eval-path finetune/dataset/eval.jsonl --output /tmp/demo_results.json

# 6. Проверка эскалаций
cat finetune/routing/routing_results.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"Escalated: {d['routing_statistics']['expensive_model_count']}/{d['routing_statistics']['total_examples']}\")"

# 7. Проверка savings
cat finetune/routing/routing_results.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"Cost savings: {d['cost_statistics']['cost_savings_vs_all_expensive']:.2f}%\")"
```

---

**Готово к презентации!** 🚀