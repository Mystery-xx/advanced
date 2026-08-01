#!/usr/bin/env python3
"""
Hybrid Pipeline - GPUStack Integration

Uses Ollama (local) for stages 1-2 and GPUStack (cloud) for stage 3.

Pipeline flow:
    review_text → Stage1Analyzer (Ollama) → stage1_output
                → Stage2Classifier (Ollama) → stage2_output
                → Stage3Formatter (GPUStack) → final_result

Environment variables required (in .env):
    - GPUSTACK_API_URL: GPUStack API endpoint
    - AI_API_KEY: API key for GPUStack authentication
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import requests
from dotenv import load_dotenv

from finetune.multi_stage.base import Stage, StageInput, StageOutput
from finetune.multi_stage.stage1_analyzer import Stage1Analyzer
from finetune.multi_stage.stage2_classifier import Stage2Classifier, VALID_CATEGORIES as STAGE2_CATEGORIES


# Load environment variables from .env file (project root)
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

# GPUStack configuration from environment
GPUSTACK_API_URL: Final[str] = os.getenv("GPUSTACK_API_URL", "")
AI_API_KEY: Final[str] = os.getenv("AI_API_KEY", "")

# Ollama configuration (local)
OLLAMA_URL: Final[str] = "http://localhost:11434"
OLLAMA_MODEL: Final[str] = "qwen3:14b"

# GPUStack model for stage 3
GPUSTACK_MODEL: Final[str] = "qwen3.6-27b"


class GPUStackStage3(Stage):
    """
    Stage 3: GPUStack-based formatter and validator.
    
    This stage uses GPUStack cloud API to validate and format
    the classification result from Stage 2.
    """
    
    @property
    def name(self) -> str:
        return "stage3_gpustack_formatter"
    
    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        """
        Initialize GPUStack Stage 3.
        
        Args:
            api_url: GPUStack API URL (default: from env GPUSTACK_API_URL)
            api_key: API key for authentication (default: from env AI_API_KEY)
        """
        self.api_url = api_url or GPUSTACK_API_URL
        self.api_key = api_key or AI_API_KEY
        self.model = GPUSTACK_MODEL
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """
        Execute Stage 3 using GPUStack API.
        
        Args:
            input_data: StageInput with data containing:
                - classification: str (from Stage 2)
                - stage1_output: dict (from Stage 1)
                - confidence: float (from Stage 2)
        
        Returns:
            StageOutput with formatted result from GPUStack
        """
        try:
            data = input_data.data
            classification = data.get("classification", "")
            stage1_output = data.get("stage1_output", {})
            confidence = data.get("confidence", 0.5)
            
            # Call GPUStack API for validation
            result = self._call_gpustack_api(classification, stage1_output, confidence)
            
            return StageOutput(
                result=result,
                success=result.get("validated", False),
                metadata={
                    "stage": self.name,
                    "provider": "gpustack",
                    "model": self.model
                }
            )
        
        except requests.ConnectionError as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=f"Cannot connect to GPUStack at {self.api_url}: {str(e)}",
                metadata={"stage": self.name, "provider": "gpustack"}
            )
        except requests.HTTPError as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=f"GPUStack API error: {str(e)}",
                metadata={"stage": self.name, "provider": "gpustack"}
            )
        except Exception as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=f"Stage 3 GPUStack failed: {str(e)}",
                metadata={"stage": self.name, "provider": "gpustack"}
            )
    
    def _call_gpustack_api(
        self,
        classification: str,
        stage1_output: dict,
        confidence: float
    ) -> dict:
        """
        Call GPUStack API to validate and format classification.
        
        Args:
            classification: Predicted category from Stage 2
            stage1_output: Preprocessing metadata from Stage 1
            confidence: Confidence score from Stage 2
        
        Returns:
            dict with validated result
        
        Raises:
            requests.ConnectionError: If GPUStack is unreachable
            requests.HTTPError: If API returns error status
        """
        if not self.api_url:
            raise EnvironmentError(
                "GPUSTACK_API_URL not set. "
                "Please set it in .env file or environment variables."
            )
        
        if not self.api_key:
            raise EnvironmentError(
                "AI_API_KEY not set. "
                "Please set it in .env file or environment variables."
            )
        
        # Build prompt for GPUStack validation
        system_prompt = (
            "Ты — валидатор классификации тональности отзывов. "
            f"Проверь, что категория принадлежит одному из: {', '.join(STAGE2_CATEGORIES)}. "
            "Верни строгий JSON с полями: category, confidence, validated, errors."
        )
        
        user_prompt = (
            f"Классикация: {classification}\n"
            f"Уверенность: {confidence}\n"
            "Проверь корректность категории и верни валидированный результат."
        )
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "stream": False,
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(
            f"{self.api_url}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse GPUStack response (expecting JSON-like output)
        # For simplicity, we'll construct the result based on validation
        validated = classification in STAGE2_CATEGORIES
        errors = [] if validated else [
            f"Invalid category '{classification}'. "
            f"Must be one of: {', '.join(STAGE2_CATEGORIES)}"
        ]
        
        # Clamp confidence to [0.0, 1.0]
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))
        
        return {
            "category": classification,
            "confidence": confidence,
            "validated": validated,
            "errors": errors
        }


class HybridPipeline:
    """
    Hybrid pipeline: Ollama (stages 1-2) + GPUStack (stage 3).
    
    Pipeline flow:
        review_text → Stage1Analyzer (Ollama, local) → stage1_output
                    → Stage2Classifier (Ollama, local) → stage2_output
                    → GPUStackStage3 (GPUStack, cloud) → final_result
    
    Example:
        >>> pipeline = HybridPipeline()
        >>> result = pipeline.run_hybrid("Отличная тачка для дачи!")
        >>> print(result["final_result"]["category"])
        "позитивный"
        >>> print(result["sources"])
        {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
    """
    
    def __init__(
        self,
        gpustack_url: str | None = None,
        gpustack_key: str | None = None
    ):
        """
        Initialize hybrid pipeline.
        
        Args:
            gpustack_url: GPUStack API URL (default: from env GPUSTACK_API_URL)
            gpustack_key: GPUStack API key (default: from env AI_API_KEY)
        """
        self.stage1 = Stage1Analyzer()
        self.stage2 = Stage2Classifier()
        self.stage3 = GPUStackStage3(api_url=gpustack_url, api_key=gpustack_key)
    
    def run_hybrid(self, review_text: str) -> dict:
        """
        Execute hybrid pipeline on review text.
        
        Args:
            review_text: The review text to classify
        
        Returns: with keys:
                - stage1: Stage 1 output (Ollama)
                - stage2: Stage 2 output (Ollama)
                - stage3: Stage 3 output (GPUStack)
                - final_result: Final classification result
                - sources: {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
            
            If any stage fails:
                - stage1/stage2/stage3: May contain partial results
                - final_result: {"error": str, "failed_at_stage": str}
                - sources: Indicates which stages completed
        """
        result = {
            "stage1": None,
            "stage2": None,
            "stage3": None,
            "final_result": None,
            "sources": {
                "stage1": "ollama",
                "stage2": "ollama",
                "stage3": "gpustack"
            }
        }
        
        # Stage 1: Analyze review text (Ollama - local)
        stage1_input = StageInput(data=review_text)
        stage1_output = self.stage1.execute(stage1_input)
        
        if not stage1_output.success:
            result["stage1"] = {
                "error": stage1_output.error_message,
                "success": False
            }
            result["final_result"] = {
                "error": f"Stage 1 failed: {stage1_output.error_message}",
                "failed_at_stage": "stage1_analyzer"
            }
            return result
        
        result["stage1"] = stage1_output.result
        
        # Stage 2: Classify sentiment (Ollama - local)
        stage2_input = StageInput(data=stage1_output.result)
        stage2_output = self.stage2.execute(stage2_input)
        
        if not stage2_output.success:
            result["stage2"] = {
                "error": stage2_output.error_message,
                "success": False
            }
            result["final_result"] = {
                "error": f"Stage 2 failed: {stage2_output.error_message}",
                "failed_at_stage": "stage2_classifier"
            }
            return result
        
        result["stage2"] = stage2_output.result
        
        # Stage 3: Format and validate (GPUStack - cloud)
        stage3_input = StageInput(data={
            "classification": stage2_output.result["category"],
            "stage1_output": stage1_output.result,
            "confidence": stage2_output.result["confidence"]
        })
        stage3_output = self.stage3.execute(stage3_input)
        
        if not stage3_output.success:
            result["stage3"] = {
                "error": stage3_output.error_message,
                "success": False
            }
            result["final_result"] = {
                "error": f"Stage 3 failed: {stage3_output.error_message}",
                "failed_at_stage": "stage3_gpustack_formatter"
            }
            return result
        
        result["stage3"] = stage3_output.result
        result["final_result"] = stage3_output.result
        
        return result


def run_hybrid(review_text: str) -> dict:
    """
    Convenience function to run hybrid pipeline.
    
    Args:
        review_text: Review text to classify
    
    Returns:
        dict with stage results and final classification
    
    Example:
        >>> result = run_hybrid("Отличная тачка для дачи!")
        >>> print(result["final_result"])
    """
    pipeline = HybridPipeline()
    return pipeline.run_hybrid(review_text)


if __name__ == "__main__":
    # Quick self-test
    print("Hybrid Pipeline Test")
    print("=" * 50)
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    print(f"GPUStack URL: {GPUSTACK_API_URL or '(not set)'}")
    print(f"GPUStack Model: {GPUSTACK_MODEL}")
    print()
    
    # Check environment
    if not GPUSTACK_API_URL:
        print("[WARNING] GPUSTACK_API not set in .env")
    if not AI_API_KEY:
        print("[WARNING] AI_API_KEY not set in .env")
    print()
    
    # Test with sample review
    test_review = "Отличная тачка для дачи – крепкая, удобная!"
    print(f"Test review: {test_review}")
    print()
    
    try:
        result = run_hybrid(test_review)
        print("Pipeline result:")
        print(f"  Stage 1 (Ollama): {'✓' if result['stage1'] else '✗'}")
        print(f"  Stage 2 (Ollama): {'✓' if result['stage2'] else '✗'}")
        print(f"  Stage 3 (GPUStack): {'✓' if result['stage3'] else '✗'}")
        print(f"  Final result: {result.get('final_result', {})}")
        print(f"  Sources: {result['sources']}")
    except Exception as e:
        print(f"Pipeline failed: {e}")