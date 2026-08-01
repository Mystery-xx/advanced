#!/usr/bin/env python3
"""Наглядная демонстрация 3-этапного пайплайна классификации тональности."""

from finetune.multi_stage.pipeline import MultiStagePipeline


def demo(text, label):
    print(f"\n{'='*60}")
    print(f"  ОТЗЫВ: {label}")
    print(f"{'='*60}")
    print(f"  «{text}»\n")

    r = MultiStagePipeline().run_pipeline(text)

    print(f"📊 STAGE 1 — Анализ")
    print(f"   Позитивные маркеры: {r['stage1']['markers']['positive']}")
    print(f"   Негативные маркеры: {r['stage1']['markers']['negative']}")
    print(f"   Слов: {r['stage1']['metadata']['word_count']}, язык: {r['stage1']['metadata']['language']}")

    print(f"\n🎯 STAGE 2 — Классификация")
    print(f"   Категория: {r['stage2']['category']} (уверенность: {r['stage2']['confidence']:.2f})")

    print(f"\n✅ STAGE 3 — Валидация")
    print(f"   Валидно: {r['stage3']['validated']}")
    print(f"   Финальная категория: {r['stage3']['category']}")
    print(f"   Финальная уверенность: {r['stage3']['confidence']:.2f}")

    print(f"\n🏁 ИТОГ: {r['final_result']['category']} | {r['final_result']['confidence']:.2f}")


if __name__ == "__main__":
    demo("Отличный товар! Быстрая доставка, рекомендую всем!", "ПОЗИТИВНЫЙ")
    demo("Ужасное качество, сломалось через день. Не рекомендую!", "НЕГАТИВНЫЙ")
    demo("Товар получили. Упаковка целая. Работает нормально.", "НЕЙТРАЛЬНЫЙ")
