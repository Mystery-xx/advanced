# Датасет классификации тональности отзывов

## Описание

Датасет для fine-tuning языковой модели на задачу классификации тональности отзывов покупателей. Содержит 100 обзоров товаров категории «садовые тачки» по 4 категориям тональности.

## Состав

| Файл | Записей | Описание |
|------|---------|----------|
| `train.jsonl` | 80 | Обучающая выборка (80%) |
| `eval.jsonl` | 20 | Оценка модели (20%) |
| `validate.py` | — | Скрипт валидации формата |

## Формат данных

Каждая строка — JSON в формате instruction-tuning:

```json
{
  "messages": [
    {"role": "system", "content": "Ты — классификатор тональности отзывов..."},
    {"role": "user", "content": "текст отзыва"},
    {"role": "assistant", "content": "категория"}
  ]
}
```

## Категории

| Категория | Описательный диапазон | Оценок |
|-----------|------------------------|--------|
| `крайне негативный` | 1-2★ | 25 |
| `негативный` | 2-3★ | 25 |
| `нейтральный` | 4★ | 25 |
| `позитивный` | 5★ | 25 |

## Источники данных

- **Реальные отзывы**: 46 из 66 (отфильтрованы по ≥20 слов, собраны с tver.lemanapro.ru)
- **Синтетические отзывы**: 54 (сгенерированы LLM, имитируют стиль реальных отзывов)
- **Random seed**: 42 (воспроизводимый shuffle и split)

## Требования к качеству

- ✅ Все отзывы ≥ 20 слов
- ✅ Баланс: 25 отзывов на категорию
- ✅ Сплит: train 80% (80), eval 20% (20)
- ✅ Формат JSONL, валидный JSON на каждой строке
- ✅ System prompt в каждом примере

## Валидация

```bash
# Запуск валидации
python3 test-project/finetune/dataset/validate.py

# С кастомным путём
python3 test-project/finetune/dataset/validate.py /путь/к/dataset

# Переменная окружения
DATASET_DIR=/путь/к/dataset python3 test-project/finetune/dataset/validate.py
```

## Fine-tuning

Подходит для fine-tuning через:
- OpenAI API (fine-tuning endpoint)
- Hugging Face `transformers` (SFTTrainer)
- LoRA / QLoRA адаптер
- VLLM / Together AI / Replicate

## Примеры использования

```python
# Загрузка датасета
import json

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

train_data = load_jsonl("test-project/finetune/dataset/train.jsonl")
eval_data = load_jsonl("test-project/finetune/dataset/eval.jsonl")

print(f"Train: {len(train_data)}, Eval: {len(eval_data)}")
```

## Метадата

- **Дата создания**: 2026-07-29
- **Всего отзывов**: 100
- **Реальная доля**: 46% train, 30% eval
- **Синтетическая доля**: 54% train, 70% eval
