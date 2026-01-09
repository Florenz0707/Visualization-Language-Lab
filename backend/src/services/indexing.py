"""Spatial and temporal indexing utilities for optimizing geospatial queries.

This module provides:
- Spatial indexing using rtree for bounding box queries
- Temporal indexing using sorted structures for time range queries
"""

import bisect
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import shape

try:
    import rtree
    from rtree.index import Index as RTreeIndex

    RTREE_AVAILABLE = True
except ImportError:
    RTREE_AVAILABLE = False
    RTreeIndex = None


class SpatialIndex:
    """Spatial index for GeoJSON features using R-tree.

    Enables efficient bounding box queries on geographic features.
    """

    def __init__(self):
        """Initialize spatial index."""
        if not RTREE_AVAILABLE:
            raise ImportError(
                "rtree library is required for spatial indexing. "
                "Install with: pip install rtree"
            )
        self.idx: RTreeIndex = rtree.index.Index()
        self.features: List[Dict[str, Any]] = []

    def build_from_features(self, features: List[Dict[str, Any]]) -> None:
        """Build spatial index from GeoJSON features.

        Args:
            features: List of GeoJSON feature dicts with geometry
        """
        self.features = features
        for i, feature in enumerate(features):
            geom = feature.get("geometry")
            if not geom:
                continue
            try:
                bounds = shape(geom).bounds  # (minx, miny, maxx, maxy)
                self.idx.insert(i, bounds)
            except Exception:
                # Skip features with invalid geometry
                continue

    def query_bbox(
        self, bbox: Tuple[float, float, float, float]
    ) -> List[Dict[str, Any]]:
        """Query features intersecting with bounding box.

        Args:
            bbox: Bounding box as (minx, miny, maxx, maxy)

        Returns:
            List of features intersecting the bbox
        """
        indices = list(self.idx.intersection(bbox))
        return [self.features[i] for i in indices if i < len(self.features)]

    def clear(self) -> None:
        """Clear the spatial index."""
        self.idx = rtree.index.Index()
        self.features = []


class TemporalIndex:
    """Temporal index for time-based queries using sorted date lists.

    Enables efficient time range queries using binary search.
    """

    def __init__(self, date_field: str = "date"):
        """Initialize temporal index.

        Args:
            date_field: Name of the date field in feature properties
        """
        self.date_field = date_field
        self.sorted_dates: List[Tuple[date, int]] = []  # (date, feature_index)
        self.features: List[Dict[str, Any]] = []

    def build_from_features(self, features: List[Dict[str, Any]]) -> None:
        """Build temporal index from GeoJSON features.

        Args:
            features: List of GeoJSON feature dicts with date properties
        """
        self.features = features
        date_index_pairs = []

        for i, feature in enumerate(features):
            props = feature.get("properties", {})
            date_str = props.get(self.date_field)
            if not date_str:
                continue

            try:
                dt = self._parse_date(date_str)
                if dt:
                    date_index_pairs.append((dt, i))
            except Exception:
                continue

        # Sort by date for efficient binary search
        self.sorted_dates = sorted(date_index_pairs, key=lambda x: x[0])

    def query_range(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Query features within time range.

        Args:
            start: Start date (inclusive), None for no lower bound
            end: End date (inclusive), None for no upper bound

        Returns:
            List of features within the time range
        """
        if not self.sorted_dates:
            return []

        # Extract just the dates for binary search
        dates_only = [d for d, _ in self.sorted_dates]

        # Find start index using binary search
        if start:
            start_idx = bisect.bisect_left(dates_only, start)
        else:
            start_idx = 0

        # Find end index using binary search
        if end:
            # bisect_right to include the end date
            end_idx = bisect.bisect_right(dates_only, end)
        else:
            end_idx = len(self.sorted_dates)

        # Extract features in range
        result_indices = [idx for _, idx in self.sorted_dates[start_idx:end_idx]]
        return [self.features[i] for i in result_indices if i < len(self.features)]

    @staticmethod
    def _parse_date(date_str: str) -> Optional[date]:
        """Parse date string to date object.

        Args:
            date_str: ISO format date string

        Returns:
            Parsed date or None if parsing fails
        """
        try:
            return datetime.fromisoformat(date_str).date()
        except Exception:
            return None

    def clear(self) -> None:
        """Clear the temporal index."""
        self.sorted_dates = []
        self.features = []


class SpatioTemporalIndex:
    """Combined spatial and temporal index for efficient multi-dimensional queries."""

    def __init__(self, date_field: str = "date"):
        """Initialize combined index.

        Args:
            date_field: Name of the date field in feature properties
        """
        self.spatial_index = SpatialIndex() if RTREE_AVAILABLE else None
        self.temporal_index = TemporalIndex(date_field)
        self.features: List[Dict[str, Any]] = []

    def build_from_features(self, features: List[Dict[str, Any]]) -> None:
        """Build both spatial and temporal indices.

        Args:
            features: List of GeoJSON feature dicts
        """
        self.features = features
        if self.spatial_index:
            self.spatial_index.build_from_features(features)
        self.temporal_index.build_from_features(features)

    def query(
        self,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Query features by spatial and/or temporal constraints.

        Args:
            bbox: Bounding box as (minx, miny, maxx, maxy)
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            List of features matching all provided constraints
        """
        # If no constraints, return all features
        if bbox is None and start is None and end is None:
            return self.features

        # Apply spatial filter if bbox provided
        if bbox and self.spatial_index:
            spatial_results = self.spatial_index.query_bbox(bbox)
            if start is None and end is None:
                return spatial_results
            # Need to further filter by time
            result_set = set(id(f) for f in spatial_results)
            temporal_results = self.temporal_index.query_range(start, end)
            return [f for f in temporal_results if id(f) in result_set]

        # Apply temporal filter only
        if start or end:
            return self.temporal_index.query_range(start, end)

        return self.features

    def clear(self) -> None:
        """Clear all indices."""
        if self.spatial_index:
            self.spatial_index.clear()
        self.temporal_index.clear()
        self.features = []
