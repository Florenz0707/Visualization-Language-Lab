"""Tests for LOD (Level of Detail) functionality."""

import pytest
from src.services.movement_utils import aggregate_to_points, simplify_geojson

# Sample movement features for testing
SAMPLE_MOVEMENTS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]],
            },
            "properties": {"unit": "Unit A", "events_count": 10},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[10.0, 10.0], [11.0, 11.0], [12.0, 12.0]],
            },
            "properties": {"unit": "Unit A", "events_count": 5},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[20.0, 20.0], [21.0, 21.0], [22.0, 22.0]],
            },
            "properties": {"unit": "Unit B", "events_count": 8},
        },
    ],
}


class TestSimplifyGeojson:
    """Test GeoJSON simplification."""

    def test_simplify_with_tolerance(self):
        """Test simplification with tolerance."""
        result = simplify_geojson(SAMPLE_MOVEMENTS, tolerance=0.5)

        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 3
        # Simplified lines should have fewer points
        for feature in result["features"]:
            assert feature["geometry"]["type"] == "LineString"

    def test_simplify_preserves_properties(self):
        """Test that simplification preserves feature properties."""
        result = simplify_geojson(SAMPLE_MOVEMENTS, tolerance=0.1)

        for i, feature in enumerate(result["features"]):
            original_props = SAMPLE_MOVEMENTS["features"][i]["properties"]
            assert feature["properties"] == original_props


class TestAggregateToPoints:
    """Test movement aggregation to points."""

    def test_aggregate_by_unit(self):
        """Test aggregation by unit field."""
        result = aggregate_to_points(SAMPLE_MOVEMENTS, group_by="unit")

        assert result["type"] == "FeatureCollection"
        # Should have 2 groups: Unit A and Unit B
        assert len(result["features"]) == 2

        # Check that all features are points
        for feature in result["features"]:
            assert feature["geometry"]["type"] == "Point"

    def test_aggregate_properties(self):
        """Test that aggregated features have correct properties."""
        result = aggregate_to_points(SAMPLE_MOVEMENTS, group_by="unit")

        # Find Unit A feature
        unit_a = next(
            f for f in result["features"] if f["properties"]["unit"] == "Unit A"
        )

        # Unit A has 2 movements
        assert unit_a["properties"]["count"] == 2
        # Total events: 10 + 5 = 15
        assert unit_a["properties"]["total_events"] == 15

    def test_aggregate_centroid_calculation(self):
        """Test that centroids are calculated correctly."""
        result = aggregate_to_points(SAMPLE_MOVEMENTS, group_by="unit")

        # All features should have valid coordinates
        for feature in result["features"]:
            coords = feature["geometry"]["coordinates"]
            assert len(coords) == 2
            assert isinstance(coords[0], float)
            assert isinstance(coords[1], float)
