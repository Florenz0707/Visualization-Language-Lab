"""Tests for spatial and temporal indexing optimizations."""

from datetime import date

import pytest
from src.services.indexing import SpatialIndex, SpatioTemporalIndex, TemporalIndex

# Sample GeoJSON features for testing
SAMPLE_FEATURES = [
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
        "properties": {"date": "1812-06-24", "name": "Event A"},
    },
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [30.0, 40.0]},
        "properties": {"date": "1812-09-07", "name": "Event B"},
    },
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [50.0, 60.0]},
        "properties": {"date": "1812-12-14", "name": "Event C"},
    },
    {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[0.0, 0.0], [10.0, 10.0]],
        },
        "properties": {"date": "1812-07-15", "name": "Movement D"},
    },
]


class TestTemporalIndex:
    """Test temporal indexing functionality."""

    def test_build_index(self):
        """Test building temporal index from features."""
        idx = TemporalIndex(date_field="date")
        idx.build_from_features(SAMPLE_FEATURES)

        assert len(idx.sorted_dates) == 4
        # Check dates are sorted
        dates = [d for d, _ in idx.sorted_dates]
        assert dates == sorted(dates)

    def test_query_range_with_start(self):
        """Test querying with start date only."""
        idx = TemporalIndex(date_field="date")
        idx.build_from_features(SAMPLE_FEATURES)

        start = date(1812, 9, 1)
        results = idx.query_range(start=start)

        assert len(results) == 2
        names = [f["properties"]["name"] for f in results]
        assert "Event B" in names
        assert "Event C" in names

    def test_query_range_with_end(self):
        """Test querying with end date only."""
        idx = TemporalIndex(date_field="date")
        idx.build_from_features(SAMPLE_FEATURES)

        end = date(1812, 7, 31)
        results = idx.query_range(end=end)

        assert len(results) == 2
        names = [f["properties"]["name"] for f in results]
        assert "Event A" in names
        assert "Movement D" in names

    def test_query_range_with_both(self):
        """Test querying with both start and end dates."""
        idx = TemporalIndex(date_field="date")
        idx.build_from_features(SAMPLE_FEATURES)

        start = date(1812, 7, 1)
        end = date(1812, 10, 1)
        results = idx.query_range(start=start, end=end)

        assert len(results) == 2
        names = [f["properties"]["name"] for f in results]
        assert "Movement D" in names
        assert "Event B" in names


class TestSpatialIndex:
    """Test spatial indexing functionality."""

    def test_build_index(self):
        """Test building spatial index from features."""
        try:
            idx = SpatialIndex()
            idx.build_from_features(SAMPLE_FEATURES)
            assert len(idx.features) == 4
        except ImportError:
            pytest.skip("rtree not available")

    def test_query_bbox(self):
        """Test querying with bounding box."""
        try:
            idx = SpatialIndex()
            idx.build_from_features(SAMPLE_FEATURES)

            # Query bbox that should contain first two points
            bbox = (5.0, 15.0, 35.0, 45.0)
            results = idx.query_bbox(bbox)

            assert len(results) >= 2
            names = [f["properties"]["name"] for f in results]
            assert "Event A" in names
            assert "Event B" in names
        except ImportError:
            pytest.skip("rtree not available")


class TestSpatioTemporalIndex:
    """Test combined spatial and temporal indexing."""

    def test_build_index(self):
        """Test building combined index."""
        idx = SpatioTemporalIndex(date_field="date")
        idx.build_from_features(SAMPLE_FEATURES)
        assert len(idx.features) == 4

    def test_query_temporal_only(self):
        """Test querying with temporal constraint only."""
        idx = SpatioTemporalIndex(date_field="date")
        idx.build_from_features(SAMPLE_FEATURES)

        start = date(1812, 9, 1)
        results = idx.query(start=start)

        assert len(results) == 2
        names = [f["properties"]["name"] for f in results]
        assert "Event B" in names
        assert "Event C" in names

    def test_query_spatial_only(self):
        """Test querying with spatial constraint only."""
        try:
            idx = SpatioTemporalIndex(date_field="date")
            idx.build_from_features(SAMPLE_FEATURES)

            bbox = (5.0, 15.0, 35.0, 45.0)
            results = idx.query(bbox=bbox)

            assert len(results) >= 2
        except ImportError:
            pytest.skip("rtree not available")

    def test_query_combined(self):
        """Test querying with both spatial and temporal constraints."""
        try:
            idx = SpatioTemporalIndex(date_field="date")
            idx.build_from_features(SAMPLE_FEATURES)

            bbox = (5.0, 15.0, 35.0, 45.0)
            start = date(1812, 6, 1)
            end = date(1812, 8, 1)
            results = idx.query(bbox=bbox, start=start, end=end)

            # Should only get Event A (in bbox and time range)
            assert len(results) >= 1
            names = [f["properties"]["name"] for f in results]
            assert "Event A" in names
        except ImportError:
            pytest.skip("rtree not available")
