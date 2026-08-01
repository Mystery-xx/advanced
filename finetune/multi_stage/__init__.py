"""
Multi-stage inference pipeline module.

This module provides a framework for building 3-stage inference pipelines
with standardized interfaces and composable stages.
"""

from finetune.multi_stage.base import Stage, StageInput, StageOutput

__all__ = [
    "Stage",
    "StageInput",
    "StageOutput",
]