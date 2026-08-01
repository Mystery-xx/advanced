#!/usr/bin/env python3
"""
Base classes for multi-stage inference pipeline.

This module provides abstract base classes for implementing a 3-stage
inference pipeline with standardized interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StageInput:
    """Input data passed between stages."""

    data: Any
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StageOutput:
    """Output data from a stage."""

    result: Any
    success: bool
    error_message: str = ""
    metadata: dict = field(default_factory=dict)


class Stage(ABC):
    """
    Abstract base class for a pipeline stage.

    Each stage in the 3-stage inference pipeline must implement
    this interface to ensure consistent input/output handling.

    Example:
        >>> class PreprocessingStage(Stage):
        ...     def execute(self, input_data: StageInput) -> StageOutput:
        ...         # Process input_data
        ...         return StageOutput(result=processed_data, success=True)
    """

    @abstractmethod
    def execute(self, input_data: StageInput) -> StageOutput:
        """
        Execute the stage logic.

        Args:
            input_data: Input data from previous stage or initial input

        Returns:
            StageOutput with result and execution status

        Raises:
            Exception: Stage-specific errors (should be caught and
                      returned as StageOutput with success=False)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stage name for logging and debugging."""
        pass