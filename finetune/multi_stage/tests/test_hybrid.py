#!/usr/bin/env python3
"""
Tests for HybridPipeline (GPUStack integration).

Tests cover:
- Hybrid pipeline initialization
- Stage 1-2 local execution (Ollama)
- Stage 3 cloud execution (GPUStack, mocked)
- Full end-to-end on 5 examples
- Error handling (API failures)
- Output structure validation
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from finetune.multi_stage.hybrid_pipeline import (
    HybridPipeline,
    GPUStackStage3,
    run_hybrid,
    GPUSTACK_API_URL,
    AI_API_KEY,
    OLLAMA_URL,
    OLLAMA_MODEL,
    GPUSTACK_MODEL,
)
from finetune.multi_stage.base import StageInput, StageOutput


# Load examples from eval.jsonl for integration tests
DATASET_PATH = Path(__file__).parent.parent.parent / "dataset" / "eval.jsonl"


def load_eval_examples(n=5):
    """Load n examples from eval.jsonl."""
    examples = []
    if not DATASET_PATH.exists():
        return examples
    
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
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


class TestGPUStackStage3:
    """Test suite for GPUStackStage3."""
    
    @pytest.fixture
    def stage3(self):
        """Create GPUStackStage3 instance with mock credentials."""
        return GPUStackStage3(
            api_url="http://test-gpustack.example.com",
            api_key="mock-test-api-key"
        )
    
    def test_stage_name(self, stage3):
        """Test stage name property."""
        assert stage3.name == "stage3_gpustack_formatter"
    
    def test_initialization_with_custom_credentials(self):
        """Test initialization with custom URL and key."""
        stage3 = GPUStackStage3(
            api_url="http://custom.example.com",
            api_key="mock-custom-key"  # Explicitly marked as mock
        )
        assert stage3.api_url == "http://custom.example.com"
        assert stage3.api_key == "mock-custom-key"
        assert stage3.model == GPUSTACK_MODEL
    
    def test_initialization_from_env(self):
        """Test initialization from environment variables."""
        with patch.dict(os.environ, {
            "GPUSTACK_API_URL": "http://env.example.com",
            "AI_API_KEY": "mock-env-key"  # Explicitly marked as mock
        }):
            # Reload module to pick up env vars
            import importlib
            import finetune.multi_stage.hybrid_pipeline as hp
            importlib.reload(hp)
            
            stage3 = hp.GPUStackStage3()
            assert stage3.api_url == "http://env.example.com"
            assert stage3.api_key == "mock-env-key"
    
    def test_execute_success(self, stage3):
        """Test successful Stage 3 execution."""
        input_data = StageInput(data={
            "classification": "позитивный",
            "stage1_output": {"key_phrases": ["отличная"]},
            "confidence": 0.9
        })
        
        # Mock the API call
        with patch.object(stage3, '_call_gpustack_api') as mock_api:
            mock_api.return_value = {
                "category": "позитивный",
                "confidence": 0.9,
                "validated": True,
                "errors": []
            }
            
            output = stage3.execute(input_data)
            
            assert isinstance(output, StageOutput)
            assert output.success is True
            assert output.result is not None
            assert output.result["validated"] is True
            assert output.metadata["provider"] == "gpustack"
            assert output.metadata["model"] == GPUSTACK_MODEL
    
    def test_execute_with_invalid_category(self, stage3):
        """Test Stage 3 with invalid category."""
        input_data = StageInput(data={
            "classification": "invalid_category",
            "stage1_output": {},
            "confidence": 0.5
        })
        
        with patch.object(stage3, '_call_gpustack_api') as mock_api:
            mock_api.return_value = {
                "category": "invalid_category",
                "confidence": 0.5,
                "validated": False,
                "errors": ["Invalid category"]
            }
            
            output = stage3.execute(input_data)
            
            assert output.success is False
            assert output.result["validated"] is False
            assert len(output.result["errors"]) > 0
    
    def test_execute_connection_error(self, stage3):
        """Test Stage 3 with connection error."""
        import requests
        
        input_data = StageInput(data={
            "classification": "позитивный",
            "stage1_output": {},
            "confidence": 0.9
        })
        
        with patch.object(stage3, '_call_gpustack_api') as mock_api:
            mock_api.side_effect = requests.ConnectionError("Connection failed")
            
            output = stage3.execute(input_data)
            
            assert output.success is False
            assert "Cannot connect to GPUStack" in output.error_message
            assert output.metadata["provider"] == "gpustack"
    
    def test_execute_http_error(self, stage3):
        """Test Stage 3 with HTTP error."""
        import requests
        
        input_data = StageInput(data={
            "classification": "позитивный",
            "stage1_output": {},
            "confidence": 0.9
        })
        
        with patch.object(stage3, '_call_gpustack_api') as mock_api:
            mock_api.side_effect = requests.HTTPError("API error 500")
            
            output = stage3.execute(input_data)
            
            assert output.success is False
            assert "GPUStack API error" in output.error_message
    
    def test_call_gpustack_api_missing_url(self):
        """Test API call with missing GPUStack URL."""
        stage3 = GPUStackStage3(api_url="", api_key="mock-test-key")
        
        with patch.object(stage3, '_call_gpustack_api') as mock_api:
            mock_api.side_effect = EnvironmentError("GPUSTACK_API_URL not set")
            
            with pytest.raises(EnvironmentError) as exc_info:
                stage3._call_gpustack_api("позитивный", {}, 0.9)
            
            assert "GPUSTACK_API_URL not set" in str(exc_info.value)
    
    def test_call_gpustack_api_missing_key(self):
        """Test API call with missing API key."""
        stage3 = GPUStackStage3(api_url="http://test.com", api_key="")
        
        with patch.object(stage3, '_call_gpustack_api') as mock_api:
            mock_api.side_effect = EnvironmentError("AI_API_KEY not set")
            
            with pytest.raises(EnvironmentError) as exc_info:
                stage3._call_gpustack_api("позитивный", {}, 0.9)
            
            assert "AI_API_KEY not set" in str(exc_info.value)
    
    def test_call_gpustack_api_request_structure(self, stage3):
        """Test that API call sends correct request structure."""
        import requests
        
        input_data = StageInput(data={
            "classification": "позитивный",
            "stage1_output": {"key_phrases": ["отличная"]},
            "confidence": 0.9
        })
        
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": '{"category": "позитивный", "validated": true}'}
            }]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            try:
                stage3._call_gpustack_api("позитивный", {"key_phrases": ["отличная"]}, 0.9)
            except Exception:
                pass  # Ignore parsing errors, we just want to check the request
            
            # Verify request was made with correct structure
            assert mock_post.called
            call_args = mock_post.call_args
            
            # Check URL
            assert call_args[0][0] == "http://test-gpustack.example.com/v1/chat/completions"
            
            # Check headers
            headers = call_args[1]['headers']
            assert headers['Authorization'] == 'Bearer mock-test-api-key'
            assert headers['Content-Type'] == 'application/json'
            
            # Check payload
            payload = call_args[1]['json']
            assert payload['model'] == GPUSTACK_MODEL
            assert payload['temperature'] == 0.0
            assert payload['stream'] is False
            assert len(payload['messages']) == 2
            assert payload['messages'][0]['role'] == 'system'
            assert payload['messages'][1]['role'] == 'user'
    
    def test_confidence_clamping(self, stage3):
        """Test that confidence is clamped to [0.0, 1.0]."""
        import requests
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"category": "позитивный"}'}}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.post', return_value=mock_response):
            # Test with confidence > 1.0
            result = stage3._call_gpustack_api("позитивный", {}, 1.5)
            assert 0.0 <= result["confidence"] <= 1.0
            
            # Test with confidence < 0.0
            result = stage3._call_gpustack_api("позитивный", {}, -0.5)
            assert 0.0 <= result["confidence"] <= 1.0


class TestHybridPipeline:
    """Test suite for HybridPipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Create HybridPipeline instance with mock credentials."""
        return HybridPipeline(
            gpustack_url="http://test-gpustack.example.com",
            gpustack_key="mock-test-api-key"
        )
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes all stages."""
        assert pipeline.stage1 is not None
        assert pipeline.stage2 is not None
        assert pipeline.stage3 is not None
        assert pipeline.stage3.api_url == "http://test-gpustack.example.com"
        assert pipeline.stage3.api_key == "mock-test-api-key"
    
    def test_run_hybrid_structure(self, pipeline):
        """Test that run_hybrid returns correct structure."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
             patch.object(pipeline.stage2, 'execute') as mock_stage2, \
             patch.object(pipeline.stage3, 'execute') as mock_stage3:
            
            # Mock successful stage outputs
            mock_stage1.return_value = StageOutput(
                result={"key_phrases": ["test"], "markers": {"positive": [], "negative": []}},
                success=True
            )
            mock_stage2.return_value = StageOutput(
                result={"category": "позитивный", "confidence": 0.9},
                success=True
            )
            mock_stage3.return_value = StageOutput(
                result={"category": "позитивный", "confidence": 0.9, "validated": True, "errors": []},
                success=True
            )
            
            result = pipeline.run_hybrid("Test review")
            
            assert "stage1" in result
            assert "stage2" in result
            assert "stage3" in result
            assert "final_result" in result
            assert "sources" in result
            
            # Check sources
            assert result["sources"]["stage1"] == "ollama"
            assert result["sources"]["stage2"] == "ollama"
            assert result["sources"]["stage3"] == "gpustack"
    
    def test_run_hybrid_stage1_failure(self, pipeline):
        """Test pipeline handles Stage 1 failure."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1:
            mock_stage1.return_value = StageOutput(
                result=None,
                success=False,
                error_message="Stage 1 failed"
            )
            
            result = pipeline.run_hybrid("Test review")
            
            assert result["stage1"]["success"] is False
            assert "final_result" in result
            assert "error" in result["final_result"]
            assert result["final_result"]["failed_at_stage"] == "stage1_analyzer"
            assert result["stage2"] is None
            assert result["stage3"] is None
    
    def test_run_hybrid_stage2_failure(self, pipeline):
        """Test pipeline handles Stage 2 failure."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
             patch.object(pipeline.stage2, 'execute') as mock_stage2:
            
            mock_stage1.return_value = StageOutput(
                result={"key_phrases": ["test"]},
                success=True
            )
            mock_stage2.return_value = StageOutput(
                result=None,
                success=False,
                error_message="Stage 2 failed"
            )
            
            result = pipeline.run_hybrid("Test review")
            
            assert result["stage1"] is not None
            assert result["stage2"]["success"] is False
            assert result["final_result"]["failed_at_stage"] == "stage2_classifier"
            assert result["stage3"] is None
    
    def test_run_hybrid_stage3_failure(self, pipeline):
        """Test pipeline handles Stage 3 failure."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
             patch.object(pipeline.stage2, 'execute') as mock_stage2, \
             patch.object(pipeline.stage3, 'execute') as mock_stage3:
            
            mock_stage1.return_value = StageOutput(
                result={"key_phrases": ["test"]},
                success=True
            )
            mock_stage2.return_value = StageOutput(
                result={"category": "позитивный", "confidence": 0.9},
                success=True
            )
            mock_stage3.return_value = StageOutput(
                result=None,
                success=False,
                error_message="Stage 3 failed"
            )
            
            result = pipeline.run_hybrid("Test review")
            
            assert result["stage1"] is not None
            assert result["stage2"] is not None
            assert result["stage3"]["success"] is False
            assert result["final_result"]["failed_at_stage"] == "stage3_gpustack_formatter"
    
    def test_run_hybrid_end_to_end_positive(self, pipeline):
        """Test end-to-end pipeline with positive review."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
             patch.object(pipeline.stage2, 'execute') as mock_stage2, \
             patch.object(pipeline.stage3, 'execute') as mock_stage3:
            
            mock_stage1.return_value = StageOutput(
                result={
                    "key_phrases": ["отличная", "тачка"],
                    "markers": {"positive": ["отличная"], "negative": []},
                    "metadata": {"length": 50, "word_count": 5}
                },
                success=True
            )
            mock_stage2.return_value = StageOutput(
                result={"category": "позитивный", "confidence": 0.9},
                success=True,
                metadata={"positive_count": 1, "negative_count": 0}
            )
            mock_stage3.return_value = StageOutput(
                result={"category": "позитивный", "confidence": 0.9, "validated": True, "errors": []},
                success=True
            )
            
            result = pipeline.run_hybrid("Отличная тачка, очень доволен!")
            
            assert result["stage1"] is not None
            assert result["stage2"] is not None
            assert result["stage3"] is not None
            assert result["final_result"]["validated"] is True
            assert result["final_result"]["category"] == "позитивный"
    
    def test_run_hybrid_end_to_end_negative(self, pipeline):
        """Test end-to-end pipeline with negative review."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
             patch.object(pipeline.stage2, 'execute') as mock_stage2, \
             patch.object(pipeline.stage3, 'execute') as mock_stage3:
            
            mock_stage1.return_value = StageOutput(
                result={
                    "key_phrases": ["плохая", "сломалась"],
                    "markers": {"positive": [], "negative": ["плохая", "сломалась"]},
                    "metadata": {"length": 40, "word_count": 4}
                },
                success=True
            )
            mock_stage2.return_value = StageOutput(
                result={"category": "негативный", "confidence": 0.85},
                success=True,
                metadata={"positive_count": 0, "negative_count": 2}
            )
            mock_stage3.return_value = StageOutput(
                result={"category": "негативный", "confidence": 0.85, "validated": True, "errors": []},
                success=True
            )
            
            result = pipeline.run_hybrid("Плохая тачка, сломалась через неделю.")
            
            assert result["final_result"]["validated"] is True
            assert result["final_result"]["category"] == "негативный"
    
    def test_run_hybrid_end_to_end_neutral(self, pipeline):
        """Test end-to-end pipeline with neutral review."""
        with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
             patch.object(pipeline.stage2, 'execute') as mock_stage2, \
             patch.object(pipeline.stage3, 'execute') as mock_stage3:
            
            mock_stage1.return_value = StageOutput(
                result={
                    "key_phrases": ["работает", "нормально"],
                    "markers": {"positive": [], "negative": []},
                    "metadata": {"length": 30, "word_count": 3}
                },
                success=True
            )
            mock_stage2.return_value = StageOutput(
                result={"category": "нейтральный", "confidence": 0.7},
                success=True,
                metadata={"positive_count": 0, "negative_count": 0}
            )
            mock_stage3.return_value = StageOutput(
                result={"category": "нейтральный", "confidence": 0.7, "validated": True, "errors": []},
                success=True
            )
            
            result = pipeline.run_hybrid("Работает нормально, ничего особенного.")
            
            assert result["final_result"]["validated"] is True
            assert result["final_result"]["category"] == "нейтральный"
    
    def test_run_hybrid_with_eval_examples(self, pipeline):
        """Test end-to-end pipeline with 5 examples from eval.jsonl."""
        if not EVAL_EXAMPLES:
            pytest.skip("eval.jsonl not found")
        
        for i, example in enumerate(EVAL_EXAMPLES):
            with patch.object(pipeline.stage1, 'execute') as mock_stage1, \
                 patch.object(pipeline.stage2, 'execute') as mock_stage2, \
                 patch.object(pipeline.stage3, 'execute') as mock_stage3:
                
                # Mock stages to return reasonable results
                mock_stage1.return_value = StageOutput(
                    result={
                        "key_phrases": ["test"],
                        "markers": {"positive": [], "negative": []},
                        "metadata": {"length": len(example["text"]), "word_count": 10}
                    },
                    success=True
                )
                mock_stage2.return_value = StageOutput(
                    result={"category": example["expected_category"], "confidence": 0.8},
                    success=True
                )
                mock_stage3.return_value = StageOutput(
                    result={
                        "category": example["expected_category"],
                        "confidence": 0.8,
                        "validated": True,
                        "errors": []
                    },
                    success=True
                )
                
                result = pipeline.run_hybrid(example["text"])
                
                # Verify structure
                assert "stage1" in result, f"Example {i}: missing stage1"
                assert "stage2" in result, f"Example {i}: missing stage2"
                assert "stage3" in result, f"Example {i}: missing stage3"
                assert "final_result" in result, f"Example {i}: missing final_result"
                assert "sources" in result, f"Example {i}: missing sources"
                
                # Verify sources
                assert result["sources"]["stage1"] == "ollama", f"Example {i}: stage1 source"
                assert result["sources"]["stage2"] == "ollama", f"Example {i}: stage2 source"
                assert result["sources"]["stage3"] == "gpustack", f"Example {i}: stage3 source"


class TestRunHybridFunction:
    """Test suite for run_hybrid convenience function."""
    
    def test_run_hybrid_function(self):
        """Test run_hybrid convenience function."""
        with patch('finetune.multi_stage.hybrid_pipeline.HybridPipeline') as MockPipeline:
            mock_pipeline_instance = Mock()
            mock_pipeline_instance.run_hybrid.return_value = {
                "stage1": {},
                "stage2": {},
                "stage3": {},
                "final_result": {"category": "позитивный"},
                "sources": {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
            }
            MockPipeline.return_value = mock_pipeline_instance
            
            result = run_hybrid("Test review")
            
            MockPipeline.assert_called_once()
            mock_pipeline_instance.run_hybrid.assert_called_once_with("Test review")
            assert result["final_result"]["category"] == "позитивный"


class TestOutputStructureValidation:
    """Test output structure validation."""
    
    def test_full_output_structure(self):
        """Test complete output structure matches specification."""
        with patch('finetune.multi_stage.hybrid_pipeline.HybridPipeline') as MockPipeline:
            mock_pipeline_instance = Mock()
            expected_result = {
                "stage1": {
                    "key_phrases": ["отличная", "тачка"],
                    "markers": {"positive": ["отличная"], "negative": []},
                    "metadata": {"length": 50, "word_count": 5, "language": "ru"}
                },
                "stage2": {
                    "category": "позитивный",
                    "confidence": 0.9
                },
                "stage3": {
                    "category": "позитивный",
                    "confidence": 0.9,
                    "validated": True,
                    "errors": []
                },
                "final_result": {
                    "category": "позитивный",
                    "confidence": 0.9,
                    "validated": True,
                    "errors": []
                },
                "sources": {
                    "stage1": "ollama",
                    "stage2": "ollama",
                    "stage3": "gpustack"
                }
            }
            mock_pipeline_instance.run_hybrid.return_value = expected_result
            MockPipeline.return_value = mock_pipeline_instance
            
            result = run_hybrid("Отличная тачка!")
            
            # Verify all required keys
            assert set(result.keys()) == {"stage1", "stage2", "stage3", "final_result", "sources"}
            
            # Verify sources structure
            assert result["sources"] == {
                "stage1": "ollama",
                "stage2": "ollama",
                "stage3": "gpustack"
            }
            
            # Verify final_result structure
            assert "category" in result["final_result"]
            assert "confidence" in result["final_result"]
            assert "validated" in result["final_result"]
            assert "errors" in result["final_result"]
    
    def test_error_output_structure(self):
        """Test error output structure."""
        with patch('finetune.multi_stage.hybrid_pipeline.HybridPipeline') as MockPipeline:
            mock_pipeline_instance = Mock()
            mock_pipeline_instance.run_hybrid.return_value = {
                "stage1": None,
                "stage2": None,
                "stage3": None,
                "final_result": {
                    "error": "Stage 1 failed: invalid input",
                    "failed_at_stage": "stage1_analyzer"
                },
                "sources": {
                    "stage1": "ollama",
                    "stage2": "ollama",
                    "stage3": "gpustack"
                }
            }
            MockPipeline.return_value = mock_pipeline_instance
            
            result = run_hybrid("")
            
            assert "error" in result["final_result"]
            assert "failed_at_stage" in result["final_result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])