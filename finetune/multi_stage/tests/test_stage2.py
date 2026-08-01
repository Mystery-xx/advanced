#!/usr/bin/env python3
"""
Tests for Stage2Classifier.

Uses examples from eval.jsonl dataset.
"""

import pytest
import json
from pathlib import Path

from finetune.multi_stage.stage2_classifier import Stage2Classifier
from finetune.multi_stage.base import StageInput, StageOutput


# Load examples from eval.jsonl
DATASET_PATH = Path(__file__).parent.parent.parent / "dataset" / "eval.jsonl"


def load_eval_examples(n=10):
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
                if user_content and category:
                    examples.append({
                        "text": user_content,
                        "expected_category": category
                    })
            if len(examples) >= n:
                break
    return examples


EVAL_EXAMPLES = load_eval_examples(10)


class TestStage2Classifier:
    """Test suite for Stage2Classifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create Stage2Classifier instance."""
        return Stage2Classifier()
    
    def test_stage_name(self, classifier):
        """Test stage name property."""
        assert classifier.name == "stage2_classifier"
    
    def test_classify_returns_valid_category_positive(self, classifier):
        """Test classification returns valid category for positive review."""
        stage1_output = {
            "key_phrases": ["тачка", "дача", "рама"],
            "markers": {"positive": ["отличная", "крепкая", "удобная"], "negative": []},
            "metadata": {"length": 100, "word_count": 20}
        }
        
        result = classifier.classify(stage1_output)
        
        assert result in ["крайне негативный", "негативный", "нейтральный", "позитивный"]
        assert result == "позитивный"
    
    def test_classify_returns_valid_category_extremely_negative(self, classifier):
        """Test classification for extremely negative review (example #6 from eval.jsonl)."""
        stage1_output = {
            "key_phrases": ["колесо", "рама", "ржавчина", "корыто"],
            "markers": {
                "positive": [],
                "negative": ["провисло", "ржавчиной", "мусора", "тишина", "недостаток"]
            },
            "metadata": {"length": 200, "word_count": 40}
        }
        
        result = classifier.classify(stage1_output)
        
        assert result in ["крайне негативный", "негативный", "нейтральный", "позитивный"]
        assert result == "крайне негативный"
    
    def test_classify_returns_valid_category_neutral(self, classifier):
        """Test classification for neutral review (example #1 from eval.jsonl)."""
        stage1_output = {
            "key_phrases": ["тачка", "колесо", "рама", "краска"],
            "markers": {
                "positive": ["работает"],
                "negative": ["минус", "ослабевают"]
            },
            "metadata": {"length": 150, "word_count": 30}
        }
        
        result = classifier.classify(stage1_output)
        
        assert result in ["крайне негативный", "негативный", "нейтральный", "позитивный"]
        assert result == "нейтральный"
    
    def test_classify_with_empty_markers(self, classifier):
        """Test classification with no sentiment markers."""
        stage1_output = {
            "key_phrases": ["тачка", "колесо"],
            "markers": {"positive": [], "negative": []},
            "metadata": {"length": 50, "word_count": 10}
        }
        
        result = classifier.classify(stage1_output)
        
        assert result == "нейтральный"
    
    def test_classify_with_single_marker(self, classifier):
        """Test classification with only one marker."""
        stage1_output = {
            "key_phrases": ["тачка"],
            "markers": {"positive": ["хорошая"], "negative": []},
            "metadata": {"length": 30, "word_count": 5}
        }
        
        result = classifier.classify(stage1_output)
        
        assert result == "нейтральный"
    
    def test_execute_stage_interface(self, classifier):
        """Test that execute method works with StageInput/StageOutput."""
        stage1_output = {
            "key_phrases": ["тачка", "дача"],
            "markers": {"positive": ["супер", "крепкая"], "negative": []},
            "metadata": {"length": 80, "word_count": 15}
        }
        
        input_data = StageInput(data=stage1_output)
        output = classifier.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is True
        assert output.result is not None
        assert "category" in output.result
        assert "confidence" in output.result
        assert output.result["category"] in ["крайне негативный", "негативный", "нейтральный", "позитивный"]
    
    def test_execute_with_invalid_input(self, classifier):
        """Test execute with non-dict input."""
        input_data = StageInput(data="invalid")  # Invalid: not a dict
        output = classifier.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is False
        assert output.error_message != ""
        assert output.result is None
    
    def test_execute_missing_markers_key(self, classifier):
        """Test execute with missing markers key."""
        input_data = StageInput(data={"key_phrases": ["тачка"]})
        output = classifier.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is False
        assert "markers" in output.error_message
        assert output.result is None
    
    def test_confidence_calculation_clear_positive(self, classifier):
        """Test confidence is high for clear positive sentiment."""
        stage1_output = {
            "key_phrases": ["тачка"],
            "markers": {"positive": ["отличная", "превосходная", "лучшая"], "negative": []},
            "metadata": {"length": 100, "word_count": 20}
        }
        
        input_data = StageInput(data=stage1_output)
        output = classifier.execute(input_data)
        
        assert output.success is True
        assert output.result["confidence"] >= 0.8
    
    def test_confidence_calculation_mixed(self, classifier):
        """Test confidence is lower for mixed sentiment."""
        stage1_output = {
            "key_phrases": ["тачка"],
            "markers": {"positive": ["хорошая"], "negative": ["спускает"]},
            "metadata": {"length": 80, "word_count": 15}
        }
        
        input_data = StageInput(data=stage1_output)
        output = classifier.execute(input_data)
        
        assert output.success is True
        assert output.result["confidence"] <= 0.7
    
    def test_eval_example_1_neutral(self, classifier):
        """Test eval.jsonl example #1 (neutral)."""
        example = EVAL_EXAMPLES[0]
        assert example["expected_category"] == "нейтральный"
        
        # Simulate Stage 1 analysis
        stage1_output = {
            "key_phrases": ["тачка", "колесо", "краска", "гайки"],
            "markers": {"positive": ["работает"], "negative": ["минус", "ослабевают"]},
            "metadata": {"length": len(example["text"]), "word_count": len(example["text"].split())}
        }
        
        result = classifier.classify(stage1_output)
        assert result == "нейтральный"
    
    def test_eval_example_4_positive(self, classifier):
        """Test eval.jsonl example #4 (positive)."""
        example = EVAL_EXAMPLES[3]
        assert example["expected_category"] == "позитивный"
        
        stage1_output = {
            "key_phrases": ["тачка", "дача", "рама", "ручки"],
            "markers": {"positive": ["отличная", "крепкая", "удобная", "выносливая", "лучших"], "negative": []},
            "metadata": {"length": len(example["text"]), "word_count": len(example["text"].split())}
        }
        
        result = classifier.classify(stage1_output)
        assert result == "позитивный"
    
    def test_eval_example_6_extremely_negative(self, classifier):
        """Test eval.jsonl example #6 (крайне негативный)."""
        example = EVAL_EXAMPLES[5]
        assert example["expected_category"] == "крайне негативный"
        
        stage1_output = {
            "key_phrases": ["колесо", "рама", "ржавчина", "корыто", "поддержка"],
            "markers": {
                "positive": [],
                "negative": ["провисло", "ржавчиной", "мусора", "тишина", "недостаток"]
            },
            "metadata": {"length": len(example["text"]), "word_count": len(example["text"].split())}
        }
        
        result = classifier.classify(stage1_output)
        assert result == "крайне негативный"
    
    def test_eval_example_8_positive(self, classifier):
        """Test eval.jsonl example #8 (positive)."""
        example = EVAL_EXAMPLES[7]
        assert example["expected_category"] == "позитивный"
        
        stage1_output = {
            "key_phrases": ["тачка", "дача", "рама", "колесо", "корыто"],
            "markers": {"positive": ["лучшая", "крепкая", "удобная", "рекомендую"], "negative": []},
            "metadata": {"length": len(example["text"]), "word_count": len(example["text"].split())}
        }
        
        result = classifier.classify(stage1_output)
        assert result == "позитивный"
    
    def test_all_eval_examples_process_successfully(self, classifier):
        """Test all 10 loaded eval examples process without errors."""
        for i, example in enumerate(EVAL_EXAMPLES):
            # Simulate Stage 1 output with varying marker counts
            pos_count = (i % 3)  # Vary positive markers
            neg_count = ((i + 1) % 3)  # Vary negative markers
            
            stage1_output = {
                "key_phrases": example["text"].split()[:5],
                "markers": {
                    "positive": ["положительный"] * pos_count,
                    "negative": ["отрицательный"] * neg_count
                },
                "metadata": {"length": len(example["text"]), "word_count": len(example["text"].split())}
            }
            
            result = classifier.classify(stage1_output)
            
            # Verify result is always a valid category
            assert result in ["крайне негативный", "негативный", "нейтральный", "позитивный"], \
                f"Example {i}: invalid category '{result}'"