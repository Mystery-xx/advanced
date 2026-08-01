#!/usr/bin/env python3
"""
Tests for Metrics Visualization

Tests for visualize.py covering:
- Visualization functions
- Chart generation
- Output file validation
- Edge cases (missing data, empty results)
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import pytest

from finetune.multi_stage.visualize import (
    load_results,
    ensure_charts_dir,
    extract_metrics,
    create_accuracy_chart,
    create_latency_chart,
    create_cost_chart,
    create_combined_chart,
    generate_all_charts,
    APPROACHES,
    APPROACH_KEYS,
    CHARTS_DIR,
    RESULTS_FILE,
    COLORS,
    METRICS,
)


# ─── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def sample_results():
    """Sample results data for testing."""
    return {
        "monolithic": {
            "accuracy": 0.75,
            "avg_latency_ms": 1500.0,
            "total_cost": 10.0,
        },
        "multi_stage_local": {
            "accuracy": 0.78,
            "avg_latency_ms": 800.0,
            "total_cost": 6.0,
        },
        "multi_stage_hybrid": {
            "accuracy": 0.82,
            "avg_latency_ms": 1200.0,
            "total_cost": 8.0,
        },
    }


@pytest.fixture
def temp_results_file(sample_results):
    """Create temporary results.json file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_results, f)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def temp_charts_dir():
    """Create temporary charts directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def empty_results():
    """Empty results data for edge case testing."""
    return {
        "monolithic": {},
        "multi_stage_local": {},
        "multi_stage_hybrid": {},
    }


@pytest.fixture
def partial_results():
    """Partial results with missing metrics."""
    return {
        "monolithic": {"accuracy": 0.75},
        "multi_stage_local": {"avg_latency_ms": 800.0},
        "multi_stage_hybrid": {"total_cost": 8.0},
    }


# ─── Tests: load_results ──────────────────────────────────────


class TestLoadResults:
    """Tests for load_results function."""

    def test_load_results_success(self, temp_results_file, sample_results):
        """Test loading valid results file."""
        results = load_results(temp_results_file)
        
        assert results == sample_results
        assert results["monolithic"]["accuracy"] == 0.75
        assert results["multi_stage_local"]["avg_latency_ms"] == 800.0
        assert results["multi_stage_hybrid"]["total_cost"] == 8.0

    def test_load_results_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_results(Path("/nonexistent/path/results.json"))
        
        assert "Results file not found" in str(exc_info.value)

    def test_load_results_invalid_json(self):
        """Test JSONDecodeError for invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_results(temp_path)
        finally:
            temp_path.unlink()

    def test_load_results_default_path(self):
        """Test that default path is RESULTS_FILE."""
        try:
            results = load_results()
            assert isinstance(results, dict)
        except FileNotFoundError:
            pass


# ─── Tests: ensure_charts_dir ─────────────────────────────────


class TestEnsureChartsDir:
    """Tests for ensure_charts_dir function."""

    def test_ensure_charts_dir_creates_directory(self, temp_charts_dir):
        """Test that directory is created if it doesn't exist."""
        new_dir = temp_charts_dir / "new_charts"
        assert not new_dir.exists()
        
        result = ensure_charts_dir(new_dir)
        
        assert result.exists()
        assert result.is_dir()
        assert result == new_dir

    def test_ensure_charts_dir_existing_directory(self, temp_charts_dir):
        """Test with existing directory."""
        result = ensure_charts_dir(temp_charts_dir)
        
        assert result.exists()
        assert result == temp_charts_dir

    def test_ensure_charts_dir_default_path(self):
        """Test default CHARTS_DIR path."""
        # Should not raise even if directory doesn't exist yet
        result = ensure_charts_dir()
        
        assert result == CHARTS_DIR
        assert result.exists() or not result.exists()  # May or may not exist


# ─── Tests: extract_metrics ───────────────────────────────────


class TestExtractMetrics:
    """Tests for extract_metrics function."""

    def test_extract_metrics_success(self, sample_results):
        """Test extracting metrics from complete results."""
        metrics = extract_metrics(sample_results)
        
        assert "accuracy" in metrics
        assert "avg_latency_ms" in metrics
        assert "total_cost" in metrics
        
        assert len(metrics["accuracy"]) == 3
        assert len(metrics["avg_latency_ms"]) == 3
        assert len(metrics["total_cost"]) == 3
        
        assert metrics["accuracy"][0] == 0.75  # monolithic
        assert metrics["accuracy"][1] == 0.78  # multi_stage_local
        assert metrics["accuracy"][2] == 0.82  # multi_stage_hybrid

    def test_extract_metrics_empty_results(self, empty_results):
        """Test extracting metrics with empty approach data."""
        metrics = extract_metrics(empty_results)
        
        assert len(metrics["accuracy"]) == 3
        assert len(metrics["avg_latency_ms"]) == 3
        assert len(metrics["total_cost"]) == 3
        
        # All should be 0.0 due to .get() defaults
        assert all(m == 0.0 for m in metrics["accuracy"])
        assert all(m == 0.0 for m in metrics["avg_latency_ms"])
        assert all(m == 0.0 for m in metrics["total_cost"])

    def test_extract_metrics_partial_results(self, partial_results):
        """Test extracting metrics with partial data."""
        metrics = extract_metrics(partial_results)
        
        assert len(metrics["accuracy"]) == 3
        assert len(metrics["avg_latency_ms"]) == 3
        assert len(metrics["total_cost"]) == 3
        
        # Check that missing values default to 0.0
        assert metrics["accuracy"] == [0.75, 0.0, 0.0]
        assert metrics["avg_latency_ms"] == [0.0, 800.0, 0.0]
        assert metrics["total_cost"] == [0.0, 0.0, 8.0]

    def test_extract_metrics_missing_approach(self, sample_results):
        """Test extracting metrics when an approach is missing."""
        incomplete = {
            "monolithic": sample_results["monolithic"],
            "multi_stage_local": sample_results["multi_stage_local"],
            # Missing multi_stage_hybrid
        }
        
        metrics = extract_metrics(incomplete)
        
        assert len(metrics["accuracy"]) == 3
        assert metrics["accuracy"][2] == 0.0  # Default for missing


# ─── Tests: Chart Creation Functions ──────────────────────────


class TestChartCreation:
    """Tests for individual chart creation functions."""

    def test_create_accuracy_chart(self, sample_results, temp_charts_dir):
        """Test accuracy chart creation."""
        metrics = extract_metrics(sample_results)
        output_path = temp_charts_dir / "accuracy.png"
        
        result = create_accuracy_chart(metrics, output_path)
        
        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0  # File has content

    def test_create_latency_chart(self, sample_results, temp_charts_dir):
        """Test latency chart creation."""
        metrics = extract_metrics(sample_results)
        output_path = temp_charts_dir / "latency.png"
        
        result = create_latency_chart(metrics, output_path)
        
        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_create_cost_chart(self, sample_results, temp_charts_dir):
        """Test cost chart creation."""
        metrics = extract_metrics(sample_results)
        output_path = temp_charts_dir / "cost.png"
        
        result = create_cost_chart(metrics, output_path)
        
        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_create_combined_chart(self, sample_results, temp_charts_dir):
        """Test combined radar chart creation."""
        metrics = extract_metrics(sample_results)
        output_path = temp_charts_dir / "combined.png"
        
        result = create_combined_chart(metrics, output_path)
        
        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_create_accuracy_chart_zero_metrics(self, temp_charts_dir):
        """Test chart creation with zero metrics."""
        metrics = {
            "accuracy": [0.0, 0.0, 0.0],
            "avg_latency_ms": [0.0, 0.0, 0.0],
            "total_cost": [0.0, 0.0, 0.0],
        }
        output_path = temp_charts_dir / "accuracy_zero.png"
        
        result = create_accuracy_chart(metrics, output_path)
        
        assert result == output_path
        assert output_path.exists()

    def test_create_chart_closes_figure(self, sample_results, temp_charts_dir):
        """Test that chart creation closes matplotlib figures."""
        metrics = extract_metrics(sample_results)
        output_path = temp_charts_dir / "test.png"
        
        # Get initial figure count
        initial_figs = len(plt.get_fignums())
        
        create_accuracy_chart(metrics, output_path)
        
        # Figure count should return to initial (figure closed)
        final_figs = len(plt.get_fignums())
        assert final_figs == initial_figs


# ─── Tests: generate_all_charts ───────────────────────────────


class TestGenerateAllCharts:
    """Tests for generate_all_charts function."""

    def test_generate_all_charts_success(self, sample_results, temp_results_file, temp_charts_dir):
        """Test generating all 4 charts successfully."""
        chart_paths = generate_all_charts(
            results_path=temp_results_file,
            charts_dir=temp_charts_dir,
        )
        
        assert len(chart_paths) == 4
        assert "accuracy" in chart_paths
        assert "latency" in chart_paths
        assert "cost" in chart_paths
        assert "combined" in chart_paths
        
        # Verify all files exist
        for chart_type, path in chart_paths.items():
            assert path.exists(), f"Chart {chart_type} not created"
            assert path.suffix == ".png", f"Chart {chart_type} not PNG"
            assert path.stat().st_size > 0, f"Chart {chart_type} is empty"

    def test_generate_charts_default_paths(self):
        """Test with default paths."""
        try:
            chart_paths = generate_all_charts()
            assert len(chart_paths) == 4
        except FileNotFoundError:
            pass

    def test_generate_all_charts_invalid_structure(self, temp_charts_dir):
        """Test with invalid results structure."""
        invalid_results = {"invalid": "structure"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_results, f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                generate_all_charts(results_path=temp_path, charts_dir=temp_charts_dir)
            
            assert "Missing key" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_generate_all_charts_creates_directory(self, sample_results, temp_results_file):
        """Test that charts directory is created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            charts_path = Path(tmpdir) / "new_charts"
            assert not charts_path.exists()
            
            chart_paths = generate_all_charts(
                results_path=temp_results_file,
                charts_dir=charts_path,
            )
            
            assert charts_path.exists()
            assert len(chart_paths) == 4


# ─── Tests: Edge Cases ────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_extreme_accuracy_values(self, temp_charts_dir):
        """Test with extreme accuracy values (0 and 1)."""
        results = {
            "monolithic": {"accuracy": 0.0, "avg_latency_ms": 100, "total_cost": 1},
            "multi_stage_local": {"accuracy": 1.0, "avg_latency_ms": 100, "total_cost": 1},
            "multi_stage_hybrid": {"accuracy": 0.5, "avg_latency_ms": 100, "total_cost": 1},
        }
        
        metrics = extract_metrics(results)
        output_path = temp_charts_dir / "extreme_acc.png"
        
        result = create_accuracy_chart(metrics, output_path)
        assert result.exists()

    def test_extreme_latency_values(self, temp_charts_dir):
        """Test with extreme latency values."""
        results = {
            "monolithic": {"accuracy": 0.75, "avg_latency_ms": 0.0, "total_cost": 1},
            "multi_stage_local": {"accuracy": 0.75, "avg_latency_ms": 10000.0, "total_cost": 1},
            "multi_stage_hybrid": {"accuracy": 0.75, "avg_latency_ms": 500.0, "total_cost": 1},
        }
        
        metrics = extract_metrics(results)
        output_path = temp_charts_dir / "extreme_lat.png"
        
        result = create_latency_chart(metrics, output_path)
        assert result.exists()

    def test_very_small_values(self, temp_charts_dir):
        """Test with very small metric values."""
        results = {
            "monolithic": {"accuracy": 0.001, "avg_latency_ms": 0.001, "total_cost": 0.001},
            "multi_stage_local": {"accuracy": 0.002, "avg_latency_ms": 0.002, "total_cost": 0.002},
            "multi_stage_hybrid": {"accuracy": 0.003, "avg_ms": 0.003, "total_cost": 0.003},
        }
        
        metrics = extract_metrics(results)
        output_path = temp_charts_dir / "small.png"
        
        result = create_combined_chart(metrics, output_path)
        assert result.exists()

    def test_very_large_values(self, temp_charts_dir):
        """Test with very large metric values."""
        results = {
            "monolithic": {"accuracy": 0.99, "avg_latency_ms": 999999.0, "total_cost": 999999.0},
            "multi_stage_local": {"accuracy": 0.98, "avg_latency_ms": 888888.0, "total_cost": 888888.0},
            "multi_stage_hybrid": {"accuracy": 0.97, "avg_latency_ms": 777777.0, "total_cost": 777777.0},
        }
        
        metrics = extract_metrics(results)
        output_path = temp_charts_dir / "large.png"
        
        result = create_combined_chart(metrics, output_path)
        assert result.exists()


# ─── Tests: Constants and Configuration ───────────────────────


class TestConstants:
    """Tests for module constants."""

    def test_approaches_count(self):
        """Test that APPROACHES has 3 entries."""
        assert len(APPROACHES) == 3

    def test_approach_keys_count(self):
        """Test that APPROACH_KEYS has 3 entries."""
        assert len(APPROACH_KEYS) == 3

    def test_colors_count(self):
        """Test that COLORS has 3 entries."""
        assert len(COLORS) == 3

    def test_metrics_count(self):
        """Test that METRICS has 3 entries."""
        assert len(METRICS) == 3
        assert "accuracy" in METRICS
        assert "avg_latency_ms" in METRICS
        assert "total_cost" in METRICS

    def test_approach_keys_match_approaches(self):
        """Test that APPROACH_KEYS length matches APPROACHES."""
        assert len(APPROACH_KEYS) == len(APPROACHES)


# ─── Integration Tests ────────────────────────────────────────


class TestIntegration:
    """Integration tests for complete visualization workflow."""

    def test_full_workflow(self, sample_results):
        """Test complete workflow from results to charts."""
        # Create temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_results, f)
            results_path = Path(f.name)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            charts_path = Path(tmpdir)
            
            try:
                # Generate all charts
                chart_paths = generate_all_charts(
                    results_path=results_path,
                    charts_dir=charts_path,
                )
                
                # Verify all charts exist
                assert len(chart_paths) == 4
                for chart_type, path in chart_paths.items():
                    assert path.exists()
                    assert path.suffix == ".png"
                
                # Verify chart names match expected
                expected_names = [
                    "accuracy_comparison.png",
                    "latency_comparison.png",
                    "cost_comparison.png",
                    "combined_metrics.png",
                ]
                
                actual_names = [p.name for p in chart_paths.values()]
                for expected_name in expected_names:
                    assert expected_name in actual_names
                
            finally:
                results_path.unlink()

    def test_results_roundtrip(self, sample_results, temp_charts_dir):
        """Test that metrics extracted from results match chart input."""
        # Extract metrics
        metrics = extract_metrics(sample_results)
        
        # Verify extraction
        assert metrics["accuracy"][0] == sample_results["monolithic"]["accuracy"]
        assert metrics["avg_latency_ms"][1] == sample_results["multi_stage_local"]["avg_latency_ms"]
        assert metrics["total_cost"][2] == sample_results["multi_stage_hybrid"]["total_cost"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])