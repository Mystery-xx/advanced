#!/usr/bin/env python3
"""
Stage 2: Sentiment Classifier

Classifies sentiment into 4 categories based on Stage 1 output.
Uses rule-based classification counting positive vs negative markers.
"""

from typing import Final

from finetune.multi_stage.base import Stage, StageInput, StageOutput


VALID_CATEGORIES: Final[tuple[str, ...]] = (
    "крайне негативный",
    "негативный",
    "нейтральный",
    "позитивный",
)


class Stage2Classifier(Stage):
    """
    Stage 2: Sentiment Classifier
    
    Classifies review sentiment into 4 categories based on Stage 1 output.
    Uses rule-based classification by counting positive vs negative markers.
    
    Classification rules:
    - If positive >> negative → позитивный
    - If negative >> positive → крайне негативный
    - If negative > positive → негативный
    - If balanced or few markers → нейтральный
    """
    
    @property
    def name(self) -> str:
        """Return the stage name."""
        return "stage2_classifier"
    
    def classify(self, stage1_output: dict) -> str:
        """
        Classify sentiment based on Stage 1 output.
        
        Args:
            stage1_output: dict from Stage1Analyzer with keys:
                - key_phrases: list of important phrases
                - markers: dict with 'positive' and 'negative' lists
                - metadata: dict with text statistics
        
        Returns:
            One of 4 categories:
            - крайне негативный
            - негативный
            - нейтральный
            - позитивный
        """
        if not stage1_output or not isinstance(stage1_output, dict):
            return "нейтральный"
        
        markers = stage1_output.get("markers", {})
        positive_markers = markers.get("positive", [])
        negative_markers = markers.get("negative", [])
        
        pos_count = len(positive_markers)
        neg_count = len(negative_markers)
        
        # Calculate ratio and total markers
        total_markers = pos_count + neg_count
        
        # If very few markers, classify as neutral
        if total_markers <= 1:
            return "нейтральный"
        
        # Calculate the difference between positive and negative
        diff = pos_count - neg_count
        
        # Classification thresholds based on marker counts
        # Extreme cases: when one type significantly dominates
        if pos_count >= 3 and neg_count == 0:
            return "позитивный"
        if neg_count >= 3 and pos_count == 0:
            return "крайне негативный"
        
        # Strong positive: positive >> negative
        if pos_count >= 2 and neg_count <= 1:
            return "позитивный"
        
        # Moderate cases based on ratio
        if pos_count > neg_count:
            # Positive dominates
            if pos_count >= 2 * neg_count and pos_count >= 2:
                return "позитивный"
            return "нейтральный"
        elif neg_count > pos_count:
            # Negative dominates - need clear dominance for негативный
            if neg_count >= 3 and pos_count <= 1:
                if neg_count >= 4:
                    return "крайне негативный"
                return "негативный"
            return "нейтральный"
        else:
            # Balanced (equal counts) → neutral
            return "нейтральный"
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """
        Execute the classification stage.
        
        Args:
            input_data: StageInput with data containing stage1_output dict
        
        Returns:
            StageOutput with classification result
        """
        try:
            stage1_output = input_data.data
            
            if not isinstance(stage1_output, dict):
                return StageOutput(
                    result=None,
                    success=False,
                    error_message="Input data must be a dict (stage1_output)"
                )
            
            # Validate stage1_output structure
            if "markers" not in stage1_output:
                return StageOutput(
                    result=None,
                    success=False,
                    error_message="stage1_output must contain 'markers' key"
                )
            
            classification = self.classify(stage1_output)
            
            # Calculate simple confidence based on marker clarity
            markers = stage1_output.get("markers", {})
            pos_count = len(markers.get("positive", []))
            neg_count = len(markers.get("negative", []))
            total = pos_count + neg_count
            
            if total == 0:
                confidence = 0.5  # Low confidence for no markers
            elif pos_count == 0 or neg_count == 0:
                confidence = 0.9  # High confidence for clear sentiment
            elif abs(pos_count - neg_count) >= 2:
                confidence = 0.8  # Good confidence for clear dominance
            else:
                confidence = 0.6  # Lower confidence for mixed signals
            
            return StageOutput(
                result={"category": classification, "confidence": confidence},
                success=True,
                metadata={
                    "stage": self.name,
                    "positive_count": pos_count,
                    "negative_count": neg_count
                }
            )
        
        except Exception as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=f"Stage 2 classification failed: {str(e)}"
            )


if __name__ == "__main__":
    # Quick self-test
    classifier = Stage2Classifier()
    
    print(f"Stage: {classifier.name}")
    print(f"Valid categories: {VALID_CATEGORIES}")
    print()
    
    # Test cases simulating Stage 1 output
    test_cases = [
        # (stage1_output, expected_category)
        ({"markers": {"positive": ["отличная", "крепкая", "удобная"], "negative": []}}, "позитивный"),
        ({"markers": {"positive": [], "negative": ["ржавчина", "провисло", "мусор", "тишина"]}}, "крайне негативный"),
        ({"markers": {"positive": ["работает"], "negative": ["минус", "ослабевают"]}}, "нейтральный"),
        ({"markers": {"positive": ["хорошая"], "negative": ["спускает"]}}, "нейтральный"),
        ({"markers": {"positive": ["супер", "крепкая", "удобная"], "negative": []}}, "позитивный"),
        ({"markers": {"positive": [], "negative": ["провисло", "ржавчиной", "мусора"]}}, "негативный"),
        ({"markers": {"positive": [], "negative": []}}, "нейтральный"),
    ]
    
    print("Running self-tests...")
    for stage1_out, expected in test_cases:
        result = classifier.classify(stage1_out)
        status = "✓" if result == expected else "✗"
        pos = len(stage1_out["markers"]["positive"])
        neg = len(stage1_out["markers"]["negative"])
        print(f"{status} classify(pos={pos}, neg={neg}) → {result} (expected: {expected})")