#!/usr/bin/env python3
"""
Multi-Stage Pipeline Orchestrator

Orchestrates 3 stages (Analyzer → Classifier → Formatter) sequentially,
handling errors between stages.
"""

from finetune.multi_stage.base import Stage, StageInput, StageOutput
from finetune.multi_stage.stage1_analyzer import Stage1Analyzer
from finetune.multi_stage.stage2_classifier import Stage2Classifier
from finetune.multi_stage.stage3_formatter import Stage3Formatter


class MultiStagePipeline:
    """
    3-stage pipeline orchestrator for review sentiment classification.
    
    Pipeline flow:
        review_text → Stage1Analyzer → stage1_output
                    → Stage2Classifier → stage2_output
                    → Stage3Formatter → final_result
    
    If any stage fails, the pipeline stops and returns an error state.
    
    Example:
        >>> pipeline = MultiStagePipeline()
        >>> result = pipeline.run_pipeline("Отличная тачка для дачи!")
        >>> print(result["final_result"]["category"])
        "позитивный"
    """
    
    def __init__(self):
        """Initialize the 3-stage pipeline with default stage instances."""
        self.stage1 = Stage1Analyzer()
        self.stage2 = Stage2Classifier()
        self.stage3 = Stage3Formatter()
    
    def run_pipeline(self, review_text: str) -> dict:
        """
        Execute the 3-stage pipeline on review text.
        
        Args:
            review_text: The review text to classify
        
        Returns:
            dict with keys:
                - stage1: Stage 1 output (key_phrases, markers, metadata)
                - stage2: Stage 2 output (category, confidence)
                - stage3: Stage 3 output (category, confidence, validated, errors)
                - final_result: Same as stage3 output (the final classification)
            
            If any stage fails, returns:
                - stage1/stage2/stage3: May contain partial results
                - final_result: {"error": str, "failed_at_stage": str}
                - "error": True flag
        
        Pipeline flow:
            1. Stage 1: analyze(review_text) → stage1_output
            2. Stage 2: classify(stage1_output) → stage2_output
            3. Stage 3: format(stage2_output, stage1_output) → final_result
        """
        result = {
            "stage1": None,
            "stage2": None,
            "stage3": None,
            "final_result": None
        }
        
        # Stage 1: Analyze review text
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
        
        # Stage 2: Classify sentiment based on Stage 1 output
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
        
        # Stage 3: Format and validate the classification result
        # Stage 3 expects: classification, stage1_output, confidence
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
                "failed_at_stage": "stage3_formatter"
            }
            return result
        
        result["stage3"] = stage3_output.result
        result["final_result"] = stage3_output.result
        
        return result