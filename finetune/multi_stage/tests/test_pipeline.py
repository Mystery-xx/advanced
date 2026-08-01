#!/usr/bin/env python3
"""
End-to-end tests for MultiStagePipeline.

Uses examples from eval.jsonl dataset to test the complete 3-stage pipeline.
"""

import pytest
import json
from pathlib import Path

from finetune.multi_stage.pipeline import MultiStagePipeline
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
                if user_content:
                    examples.append({
                        "text": user_content,
                        "expected_category": category
                    })
            if len(examples) >= n:
                break
    return examples


EVAL_EXAMPLES = load_eval_examples(10)


class TestMultiStagePipeline:
    """Test suite for MultiStagePipeline end-to-end."""
    
    def test_pipeline_initialization(self):
        """Test that pipeline initializes with 3 stages."""
        pipeline = MultiStagePipeline()
        
        assert pipeline.stage1 is not None
        assert pipeline.stage2 is not None
        assert pipeline.stage3 is not None
        assert pipeline.stage1.name == "stage1_analyzer"
        assert pipeline.stage2.name == "stage2_classifier"
        assert pipeline.stage3.name == "stage3_formatter"
    
    def test_pipeline_positive_review(self):
        """Test pipeline with clearly positive review."""
        pipeline = MultiStagePipeline()
        review = "Отличная тачка для дачи – крепкая, удобная и очень выносливая."
        
        result = pipeline.run_pipeline(review)
        
        # Check structure
        assert "stage1" in result
        assert "stage2" in result
        assert "stage3" in result
        assert "final_result" in result
        
        # Stage 1 should extract key phrases and markers
        assert result["stage1"] is not None
        assert "key_phrases" in result["stage1"]
        assert "markers" in result["stage1"]
        assert "positive" in result["stage1"]["markers"]
        assert len(result["stage1"]["markers"]["positive"]) > 0
        
        # Stage 2 should classify as позитивный
        assert result["stage2"] is not None
        assert "category" in result["stage2"]
        assert "confidence" in result["stage2"]
        assert result["stage2"]["category"] == "позитивный"
        
        # Stage 3 should validate
        assert result["stage3"] is not None
        assert result["stage3"]["validated"] is True
        assert result["stage3"]["category"] == "позитивный"
        
        # Final result should match stage3
        assert result["final_result"] == result["stage3"]
    
    def test_pipeline_negative_review(self):
        """Test pipeline with negative review."""
        pipeline = MultiStagePipeline()
        review = "Купил для огорода — тачка рабочая, но требует постоянного внимания, гайки подкручивать каждую поездку."
        
        result = pipeline.run_pipeline(review)
        
        assert result["stage2"] is not None
        assert result["stage2"]["category"] in ["негативный", "нейтральный"]
        assert result["stage3"]["validated"] is True
    
    def test_pipeline_extremely_negative_review(self):
        """Test pipeline with extremely negative review."""
        pipeline = MultiStagePipeline()
        review = "Проработала одну неделю, потом колесо пошло ходуном, рама покрылась ржавчиной, корыто провисло к колесу."
        
        result = pipeline.run_pipeline(review)
        
        assert result["stage2"] is not None
        assert "category" in result["stage2"]
        assert result["stage3"]["validated"] is True
        # Should detect negative sentiment
        assert result["stage1"]["markers"]["negative"]
    
    def test_pipeline_neutral_review(self):
        """Test pipeline with neutral review."""
        pipeline = MultiStagePipeline()
        review = "Пользовалась полгода — ни критических поломок, но и восторга нет. Для дачи сойдёт, для стройки нет."
        
        result = pipeline.run_pipeline(review)
        
        assert result["stage2"] is not None
        assert "category" in result["stage2"]
        assert result["stage3"]["validated"] is True
    
    def test_pipeline_output_structure(self):
        """Test that pipeline returns correct output structure."""
        pipeline = MultiStagePipeline()
        review = EVAL_EXAMPLES[0]["text"]
        
        result = pipeline.run_pipeline(review)
        
        # Check all required keys
        assert set(result.keys()) == {"stage1", "stage2", "stage3", "final_result"}
        
        # Check stage1 structure
        assert set(result["stage1"].keys()) == {"key_phrases", "markers", "metadata"}
        assert isinstance(result["stage1"]["key_phrases"], list)
        assert isinstance(result["stage1"]["markers"], dict)
        assert "positive" in result["stage1"]["markers"]
        assert "negative" in result["stage1"]["markers"]
        assert isinstance(result["stage1"]["metadata"], dict)
        
        # Check stage2 structure
        assert set(result["stage2"].keys()) == {"category", "confidence"}
        assert isinstance(result["stage2"]["category"], str)
        assert isinstance(result["stage2"]["confidence"], float)
        assert 0.0 <= result["stage2"]["confidence"] <= 1.0
        
        # Check stage3 structure
        assert set(result["stage3"].keys()) == {"category", "confidence", "validated", "errors"}
        assert isinstance(result["stage3"]["category"], str)
        assert isinstance(result["stage3"]["confidence"], float)
        assert isinstance(result["stage3"]["validated"], bool)
        assert isinstance(result["stage3"]["errors"], list)
        
        # Check final_result matches stage3
        assert result["final_result"] == result["stage3"]
    
    def test_pipeline_empty_input(self):
        """Test pipeline with empty input."""
        pipeline = MultiStagePipeline()
        
        result = pipeline.run_pipeline("")
        
        # Should handle gracefully
        assert result["stage1"] is not None
        assert result["stage1"]["key_phrases"] == []
        assert result["stage1"]["markers"]["positive"] == []
        assert result["stage1"]["markers"]["negative"] == []
    
    def test_pipeline_with_eval_examples(self):
        """Test pipeline with multiple examples from eval.jsonl."""
        pipeline = MultiStagePipeline()
        
        for i, example in enumerate(EVAL_EXAMPLES[:5]):
            result = pipeline.run_pipeline(example["text"])
            
            # Verify structure
            assert result["stage1"] is not None, f"Example {i}: stage1 failed"
            assert result["stage2"] is not None, f"Example {i}: stage2 failed"
            assert result["stage3"] is not None, f"Example {i}: stage3 failed"
            assert result["final_result"] is not None, f"Example {i}: final_result failed"
            
            # Verify validation
            assert result["stage3"]["validated"] is True, \
                f"Example {i}: validation failed for category {result['stage3']['category']}"
            
            # Verify category is valid
            valid_categories = ["крайне негативный", "негативный", "нейтральный", "позитивный"]
            assert result["stage3"]["category"] in valid_categories, \
                f"Example {i}: invalid category {result['stage3']['category']}"
    
    def test_pipeline_error_handling_stage1(self):
        """Test that pipeline handles Stage 1 errors correctly."""
        pipeline = MultiStagePipeline()
        
        # Test with None (should fail gracefully)
        result = pipeline.run_pipeline(None)
        
        # Should return error state
        assert result["stage1"] is not None
        assert result["final_result"] is not None
        assert "error" in result["final_result"] or "failed_at_stage" in result["final_result"]
    
    def test_pipeline_confidence_scores(self):
        """Test that confidence scores are reasonable."""
        pipeline = MultiStagePipeline()
        
        # Test with clearly positive review (should have high confidence)
        positive_review = "Супер покупка! Тачка крепкая, лёгкая, удобная. Рекомендую!"
        result = pipeline.run_pipeline(positive_review)
        
        assert result["stage2"]["confidence"] > 0.5
        assert result["stage3"]["confidence"] > 0.5
        
        # Test with mixed review (may have lower confidence)
        mixed_review = "Работает, но есть недостатки."
        result = pipeline.run_pipeline(mixed_review)
        
        assert 0.0 <= result["stage2"]["confidence"] <= 1.0
        assert 0.0 <= result["stage3"]["confidence"] <= 1.0


class TestMultiStagePipelineIntegration:
    """Integration tests using full eval.jsonl examples."""
    
    @pytest.mark.parametrize("example_idx", range(5))
    def test_pipeline_end_to_end(self, example_idx):
        """Test complete pipeline flow with eval examples."""
        pipeline = MultiStagePipeline()
        example = EVAL_EXAMPLES[example_idx]
        
        result = pipeline.run_pipeline(example["text"])
        
        # Verify complete execution
        assert result["stage1"] is not None
        assert result["stage2"] is not None
        assert result["stage3"] is not None
        assert result["final_result"] is not None
        
        # Verify final result is validated
        assert result["final_result"]["validated"] is True
        
        # Verify category is one of the valid options
        valid_categories = ["крайне негативный", "негативный", "нейтральный", "позитивный"]
        assert result["final_result"]["category"] in valid_categories
        
        # Verify confidence is in valid range
        assert 0.0 <= result["final_result"]["confidence"] <= 1.0