#!/usr/bin/env python3
"""
Stage 3: Result formatter and validator.

This module implements the final stage of the multi-stage inference pipeline.
It validates classification results and formats strict JSON output.
"""

from typing import Final

from finetune.multi_stage.base import Stage, StageInput, StageOutput
from finetune.confidence.constraint_check import LABELED_CATEGORIES, constraint_check


VALID_CATEGORIES: Final[tuple[str, ...]] = tuple(LABELED_CATEGORIES)


class Stage3Formatter(Stage):
    """
    Stage 3: Format and validate classification results.
    
    This stage validates that the classification output from Stage 2
    belongs to one of the 4 valid categories and formats the final
    JSON output with confidence and validation status.
    
    Output format:
        {
            "category": str,           # The validated category
            "confidence": float,       # Confidence score (0.0-1.0)
            "validated": bool,         # True if category is valid
            "errors": list[str]        # List of validation errors (empty if valid)
        }
    """
    
    @property
    def name(self) -> str:
        """Return the stage name."""
        return "stage3_formatter"
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """
        Execute the formatting and validation stage.
        
        Args:
            input_data: StageInput with data containing:
                - classification: str (the predicted category from Stage 2)
                - stage1_output: dict (preprocessing metadata from Stage 1)
                - confidence: float (optional, confidence from Stage 2)
        
        Returns:
            StageOutput with formatted result dict containing:
                - category: str
                - confidence: float
                - validated: bool
                - errors: list[str]
        """
        try:
            data = input_data.data
            
            # Extract classification result from Stage 2
            classification = data.get("classification", "")
            stage1_output = data.get("stage1_output", {})
            confidence = data.get("confidence", 0.5)  # Default confidence if not provided
            
            # Format and validate the result
            result = self.format(classification, stage1_output, confidence)
            
            return StageOutput(
                result=result,
                success=result["validated"],
                metadata={
                    "stage": self.name,
                    "input_classification": classification
                }
            )
        
        except Exception as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=f"Stage 3 formatting failed: {str(e)}",
                metadata={"stage": self.name}
            )
    
    def format(self, classification: str, stage1_output: dict, confidence: float = 0.5) -> dict:
        """
        Format and validate the classification result.
        
        Args:
            classification: The predicted category string from Stage 2
            stage1_output: Preprocessing metadata from Stage 1 (reserved for future use)
            confidence: Confidence score from Stage 2 (default: 0.5)
        
        Returns:
            dict with keys:
                - category (str): The classification result (normalized)
                - confidence (float): Confidence score clamped to [0.0, 1.0]
                - validated (bool): True if category is one of the 4 valid categories
                - errors (list[str]): List of validation errors (empty if validated=True)
        
        Examples:
            >>> formatter = Stage3Formatter()
            >>> formatter.format("позитивный", {})
            {'category': 'позитивный', 'confidence': 0.5, 'validated': True, 'errors': []}
            
            >>> formatter.format("отлично!", {})
            {'category': 'отлично!', 'confidence': 0.5, 'validated': False, 'errors': ['Invalid category']}
        """
        errors = []
        
        # Validate category
        constraint_result = constraint_check(classification)
        validated = constraint_result["passed"]
        
        if not validated:
            errors.append(
                f"Invalid category '{classification}'. "
                f"Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        
        # Validate confidence is in range [0.0, 1.0]
        if not isinstance(confidence, (int, float)):
            errors.append(f"Confidence must be a number, got {type(confidence).__name__}")
            confidence = 0.5
        elif confidence < 0.0 or confidence > 1.0:
            errors.append(f"Confidence must be between 0.0 and 1.0, got {confidence}")
            confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range
        
        return {
            "category": classification,
            "confidence": float(confidence),
            "validated": validated,
            "errors": errors
        }


if __name__ == "__main__":
    # Quick self-test
    formatter = Stage3Formatter()
    
    print(f"Stage: {formatter.name}")
    print(f"Valid categories: {VALID_CATEGORIES}")
    print()
    
    # Test cases
    test_cases = [
        ("крайне негативный", {}, 0.95, True),
        ("негативный", {}, 0.85, True),
        ("нейтральный", {}, 0.70, True),
        ("позитивный", {}, 0.92, True),
        ("отлично!", {}, 0.80, False),  # Invalid category
    ]
    
    print("Running self-tests...")
    for classification, stage1_out, conf, expected_valid in test_cases:
        result = formatter.format(classification, stage1_out, conf)
        status = "✓" if result["validated"] == expected_valid else "✗"
        print(f"{status} format('{classification}', conf={conf})")
        print(f"   → validated={result['validated']}, errors={result['errors']}")
        print()