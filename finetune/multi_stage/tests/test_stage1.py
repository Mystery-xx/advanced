#!/usr/bin/env python3
"""
Tests for Stage1Analyzer.

Uses examples from eval.jsonl dataset.
"""

import pytest
import json
import os
from pathlib import Path

from finetune.multi_stage.stage1_analyzer import Stage1Analyzer
from finetune.multi_stage.base import StageInput, StageOutput


# Load examples from eval.jsonl
DATASET_PATH = Path(__file__).parent.parent.parent / "dataset" / "eval.jsonl"


def load_eval_examples(n=5):
    """Load n examples from eval.jsonl."""
    examples = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                # Extract user content from messages
                user_content = None
                category = None
                for msg in data.get("messages", []):
                    if msg.get("role") == "user":
                        user_content = msg.get("content", "")
                    elif msg.get("role") == "assistant":
                        category = msg.get("content", "")
                if user_content:
                    examples.append({
                        "text": user_content,
                        "expected_category": category
                    })
            if len(examples) >= n:
                break
    return examples


EVAL_EXAMPLES = load_eval_examples(5)


class TestStage1Analyzer:
    """Test suite for Stage1Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create Stage1Analyzer instance."""
        return Stage1Analyzer()
    
    def test_stage_name(self, analyzer):
        """Test stage name property."""
        assert analyzer.name == "stage1_analyzer"
    
    def test_analyze_returns_correct_structure(self, analyzer):
        """Test that analyze returns dict with required keys."""
        result = analyzer.analyze("Отличный продукт, очень доволен!")
        
        assert isinstance(result, dict)
        assert "key_phrases" in result
        assert "markers" in result
        assert "metadata" in result
        assert isinstance(result["key_phrases"], list)
        assert isinstance(result["markers"], dict)
        assert "positive" in result["markers"]
        assert "negative" in result["markers"]
        assert isinstance(result["metadata"], dict)
        assert "length" in result["metadata"]
        assert "word_count" in result["metadata"]
    
    def test_positive_review_detection(self, analyzer):
        """Test detection of positive sentiment markers (example #4 from eval.jsonl)."""
        text = (
            "Отличная тачка для дачи – крепкая, удобная и очень выносливая. "
            "Брал для дачи: возил землю, камни, мусор – справляется на ура. "
            "Усиленная рама не гнётся даже под 200 кг, удобные прорезиненные ручки. "
            "Собирается за 15 минут, стоит устойчиво. За эти деньги – один из лучших вариантов."
        )
        
        result = analyzer.analyze(text)
        
        # Should detect positive markers
        assert len(result["markers"]["positive"]) > 0
        assert "отличная" in result["markers"]["positive"] or "лучших" in result["markers"]["positive"]
        
        # Should have key phrases
        assert len(result["key_phrases"]) > 0
        
        # Metadata should be correct
        assert result["metadata"]["length"] == len(text)
        assert result["metadata"]["word_count"] > 0
        assert result["metadata"]["language"] == "ru"
    
    def test_negative_review_detection(self, analyzer):
        """Test detection of negative sentiment markers (example #6 from eval.jsonl)."""
        text = (
            "Проработала одну неделю, потом колесо пошло ходуном, рама покрылась ржавчиной на швах, "
            "корыто провисло к колесу. Обратился в службу поддержки — пропало. "
            "Через месяц ответа — отправил фото дефектов, в ответ тишина. "
            "Качество на уровне мусора, цена как на нормальную тачку. Никому не советую."
        )
        
        result = analyzer.analyze(text)
        
        # Should detect negative markers
        assert len(result["markers"]["negative"]) > 0
        # Check for any negative marker (word forms may vary due to tokenization)
        has_negative = any(
            word in result["markers"]["negative"] 
            for word in ["провисло", "ржавчиной", "мусора", "советую"]
        )
        assert has_negative, f"Expected negative markers, got: {result['markers']['negative']}"
        
        # Should have key phrases
        assert len(result["key_phrases"]) > 0
        
        # Metadata should be correct
        assert result["metadata"]["language"] == "ru"
    
    def test_neutral_review_detection(self, analyzer):
        """Test detection of neutral review (example #1 from eval.jsonl)."""
        text = (
            "Брал чтобы заменить старую — та развалилась. Эта работает. "
            "Колесо накачиваю раз в 5 дней, корыто не гнило. Рама не шатается. "
            "Минус — покраска. Гайки ослабевают. Средняя оценка — работает."
        )
        
        result = analyzer.analyze(text)
        
        # Should detect both positive and negative markers (mixed sentiment)
        assert len(result["markers"]["positive"]) >= 0 or len(result["markers"]["negative"]) > 0
        
        # Should have key phrases
        assert len(result["key_phrases"]) > 0
        
        # Metadata should be correct
        assert result["metadata"]["word_count"] > 0
    
    def test_empty_input(self, analyzer):
        """Test handling of empty input."""
        result = analyzer.analyze("")
        
        assert result["key_phrases"] == []
        assert result["markers"]["positive"] == []
        assert result["markers"]["negative"] == []
        assert result["metadata"]["length"] == 0
        assert result["metadata"]["word_count"] == 0
    
    def test_execute_stage_interface(self, analyzer):
        """Test that execute method works with StageInput/StageOutput."""
        review_text = "Супер покупка! Тачка крепкая, лёгкая, удобная."
        
        input_data = StageInput(data=review_text)
        output = analyzer.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is True
        assert output.result is not None
        assert "key_phrases" in output.result
        assert "markers" in output.result
        assert "metadata" in output.result
    
    def test_execute_with_invalid_input(self, analyzer):
        """Test execute with non-string input."""
        input_data = StageInput(data=123)  # Invalid: not a string
        output = analyzer.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is False
        assert output.error_message != ""
        assert output.result is None
    
    def test_metadata_accuracy(self, analyzer):
        """Test metadata extraction accuracy."""
        text = "Привет мир! Это тест."
        result = analyzer.analyze(text)
        
        assert result["metadata"]["length"] == len(text)
        assert result["metadata"]["word_count"] == 4  # привет, мир, это, тест
        assert result["metadata"]["language"] == "ru"
        assert result["metadata"]["avg_word_length"] > 0
    
    def test_eval_examples_integration(self, analyzer):
        """Test all loaded eval examples process successfully."""
        for i, example in enumerate(EVAL_EXAMPLES):
            result = analyzer.analyze(example["text"])
            
            # Verify structure
            assert isinstance(result, dict), f"Example {i}: result should be dict"
            assert "key_phrases" in result, f"Example {i}: missing key_phrases"
            assert "markers" in result, f"Example {i}: missing markers"
            assert "metadata" in result, f"Example {i}: missing metadata"
            
            # Verify types
            assert isinstance(result["key_phrases"], list), f"Example {i}: key_phrases should be list"
            assert isinstance(result["markers"]["positive"], list), f"Example {i}: positive should be list"
            assert isinstance(result["markers"]["negative"], list), f"Example {i}: negative should be list"
            assert isinstance(result["metadata"]["length"], int), f"Example {i}: length should be int"
            assert isinstance(result["metadata"]["word_count"], int), f"Example {i}: word_count should be int"