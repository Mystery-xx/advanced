#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
# ]
# ///

"""
Test suite for multi_stage module initialization.

Tests:
1. All base classes can be imported without errors
2. Stage abstract base class enforces interface
3. StageInput and StageOutput dataclasses work correctly
"""

import pytest
import sys
from pathlib import Path

# Add finetune directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from finetune.multi_stage import Stage, StageInput, StageOutput


class TestModuleImports:
    """Test that all module exports can be imported."""

    def test_stage_import(self):
        """Test that Stage base class can be imported."""
        assert Stage is not None
        assert hasattr(Stage, "execute")
        assert hasattr(Stage, "name")

    def test_stage_input_import(self):
        """Test that StageInput dataclass can be imported."""
        assert StageInput is not None

    def test_stage_output_import(self):
        """Test that StageOutput dataclass can be imported."""
        assert StageOutput is not None


class TestStageInput:
    """Test StageInput dataclass."""

    def test_create_with_data_only(self):
        """Test creating StageInput with minimal arguments."""
        input_data = StageInput(data={"key": "value"})

        assert input_data.data == {"key": "value"}
        assert input_data.metadata == {}

    def test_create_with_metadata(self):
        """Test creating StageInput with metadata."""
        input_data = StageInput(
            data="test data",
            metadata={"source": "test", "version": 1}
        )

        assert input_data.data == "test data"
        assert input_data.metadata == {"source": "test", "version": 1}

    def test_immutability(self):
        """Test that StageInput is immutable (frozen)."""
        input_data = StageInput(data="test")

        with pytest.raises(Exception):  # frozen dataclass raises AttributeError or FrozenInstanceError
            input_data.data = "modified"


class TestStageOutput:
    """Test StageOutput dataclass."""

    def test_create_success_output(self):
        """Test creating successful StageOutput."""
        output = StageOutput(result={"answer": "yes"}, success=True)

        assert output.result == {"answer": "yes"}
        assert output.success is True
        assert output.error_message == ""
        assert output.metadata == {}

    def test_create_error_output(self):
        """Test creating failed StageOutput."""
        output = StageOutput(
            result=None,
            success=False,
            error_message="Stage execution failed"
        )

        assert output.result is None
        assert output.success is False
        assert output.error_message == "Stage execution failed"

    def test_create_with_metadata(self):
        """Test creating StageOutput with metadata."""
        output = StageOutput(
            result="processed",
            success=True,
            metadata={"latency_ms": 150, "stage": "preprocessing"}
        )

        assert output.metadata == {"latency_ms": 150, "stage": "preprocessing"}

    def test_immutability(self):
        """Test that StageOutput is immutable (frozen)."""
        output = StageOutput(result="test", success=True)

        with pytest.raises(Exception):
            output.success = False


class TestStageAbstractBaseClass:
    """Test Stage abstract base class interface."""

    def test_cannot_instantiate_abstract_stage(self):
        """Test that Stage cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Stage()

    def test_stage_requires_execute_method(self):
        """Test that concrete Stage must implement execute()."""
        class IncompleteStage(Stage):
            @property
            def name(self) -> str:
                return "incomplete"

        with pytest.raises(TypeError):
            IncompleteStage()

    def test_stage_requires_name_property(self):
        """Test that concrete Stage must implement name property."""
        class IncompleteStage(Stage):
            def execute(self, input_data: StageInput) -> StageOutput:
                return StageOutput(result=None, success=False)

        with pytest.raises(TypeError):
            IncompleteStage()

    def test_concrete_stage_implementation(self):
        """Test that a properly implemented Stage works."""
        class TestStage(Stage):
            @property
            def name(self) -> str:
                return "test_stage"

            def execute(self, input_data: StageInput) -> StageOutput:
                return StageOutput(
                    result=f"processed: {input_data.data}",
                    success=True
                )

        stage = TestStage()
        assert stage.name == "test_stage"

        input_data = StageInput(data="input")
        output = stage.execute(input_data)

        assert output.success is True
        assert output.result == "processed: input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])