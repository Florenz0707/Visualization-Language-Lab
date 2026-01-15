from __future__ import annotations

from datetime import date, datetime
from math import cos, pi
from typing import Tuple

import numpy as np
import xarray as xr
from fastapi import APIRouter, HTTPException, Query

DATA_ROOT = "data/noaa/berkeley"
RAW_SUBSET = "Raw_TAVG_1750_1850.nc"

router = APIRouter()


def _decimal_year_from_date(d: date) -> float:
    year = d.year
    start = date(year, 1, 1)
    day_of_year = (d - start).days  # 0-based
    # use 365-day year for interpolation (consistent with previous tooling)
    return float(year) + day_of_year / 365.0


def _month_from_decimal(dec: float) -> int:
    year = int(dec)
    frac = dec - year
    m = int(frac * 12) + 1
    if m < 1:
        m = 1
    if m > 12:
        m = 12
    return m


def _detect_lat_lon(ds: xr.Dataset) -> Tuple[str, str]:
    for lat_name in ("latitude", "lat", "y"):
        for lon_name in ("longitude", "lon", "x"):
            if lat_name in ds.coords and lon_name in ds.coords:
                return lat_name, lon_name
    # fallback to variable dims
    for v in ds.variables:
        da = ds[v]
        if hasattr(da, "coords"):
            names = list(da.coords)
            if "latitude" in names and "longitude" in names:
                return "latitude", "longitude"
    raise RuntimeError("Could not detect latitude/longitude coordinate names")


def _area_weights(lat):
    # lat can be 1D or 2D numpy array
    return np.cos(np.deg2rad(lat))


def _select_climatology_for_month(ds: xr.Dataset, month: int) -> xr.DataArray:
    """Select the climatology DataArray for the requested month.

    Handles different coordinate/dimension names such as 'month', 'month_number',
    or a months dimension as the first axis.
    """
    clim = ds["climatology"]

    # Try common coord names first
    for coord in ("month", "month_number", "month_num", "month_idx"):
        if coord in clim.coords:
            vals = clim.coords[coord].values
            try:
                if month in vals:
                    return clim.sel({coord: month})
            except Exception:
                pass
            # fallback to index selection if length permits
            if clim.sizes.get(coord, 0) >= month:
                return clim.isel({coord: month - 1})

    # Look for a dimension with 'month' in its name or common single leading dim
    for dim in clim.dims:
        if dim.lower().startswith("month"):
            if clim.sizes.get(dim, 0) >= month:
                return clim.isel({dim: month - 1})

    # fall back to any first dimension that has at least 12 entries
    if len(clim.dims) > 0:
        first = clim.dims[0]
        if clim.sizes.get(first, 0) >= month:
            return clim.isel({first: month - 1})

    raise RuntimeError(
        "Could not select climatology month; unexpected climatology layout"
    )


def _compute_scope_mean_for_time(
    absolute_da: xr.DataArray,
    lat_name: str,
    lon_name: str,
    scope: str,
    bbox: Tuple[float, float, float, float] | None,
):
    # absolute_da expected dims include lat_name and lon_name (or lat/lon 2D grid)
    # convert coords to numpy
    lat = absolute_da.coords[lat_name].values
    lon = absolute_da.coords[lon_name].values

    # handle 1D lat/lon
    if lat.ndim == 1 and lon.ndim == 1:
        weights = _area_weights(lat)  # 1D
        # broadcast to grid
        w = np.outer(weights, np.ones(len(lon)))
        data = absolute_da.values
        mask = np.ones_like(data, dtype=bool)
        if scope == "bbox" and bbox is not None:
            minlat, maxlat, minlon, maxlon = bbox
            lat_mask = (lat >= minlat) & (lat <= maxlat)
            lon_mask = (lon >= minlon) & (lon <= maxlon)
            mask = np.outer(lat_mask, lon_mask)
        w_masked = w * mask
        d = np.where(mask, data, np.nan)
        num = np.nansum(d * w_masked)
        den = (
            np.nansum(w_masked * (~np.isnan(d)))
            if False
            else np.nansum(w_masked * (~np.isnan(d)))
        )
        if den == 0:
            return float("nan")
        return float(num / den)

    # handle 2D lat array
    if lat.ndim == 2:
        # lat is 2D (curvilinear). coords might be (y,x)
        lat2 = lat
        weights = _area_weights(lat2)
        data = absolute_da.values
        mask = np.ones_like(data, dtype=bool)
        if scope == "bbox" and bbox is not None:
            minlat, maxlat, minlon, maxlon = bbox
            lon2 = lon
            mask = (
                (lat2 >= minlat)
                & (lat2 <= maxlat)
                & (lon2 >= minlon)
                & (lon2 <= maxlon)
            )
        w_masked = weights * mask
        d = np.where(mask, data, np.nan)
        num = np.nansum(d * w_masked)
        den = (
            np.nansum(w_masked * (~np.isnan(d)))
            if False
            else np.nansum(w_masked * (~np.isnan(d)))
        )
        if den == 0:
            return float("nan")
        return float(num / den)

    # unknown layout
    raise RuntimeError("Unsupported lat/lon layout for area-weighting")


@router.get("/temperature/1812")
async def get_1812_temperature(
    date_str: str = Query(..., description="ISO date in 1812 (YYYY-MM-DD)"),
    scope: str = Query("bbox", description="'global' or 'bbox'"),
    bbox: str
    | None = Query(None, description="optional bbox as minlat,maxlat,minlon,maxlon"),
):
    """Return interpolated absolute temperature for a given date in 1812.

    - `date_str`: ISO date inside 1812
    - `scope`: 'global' or 'bbox' (default 'bbox')
    - `bbox`: optional override as comma-separated `minlat,maxlat,minlon,maxlon`.

    Uses the repository's Berkeley Earth subset (`data/noaa/berkeley/Raw_TAVG_1750_1850.nc`)
    to build an absolute-temperature time series (climatology + anomaly) and linearly
    interpolates to the requested decimal-year.
    """
    try:
        qdate = datetime.fromisoformat(date_str).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if qdate.year != 1812:
        raise HTTPException(status_code=400, detail="Date must be in year 1812")

    # parse bbox if provided
    bbox_tuple = None
    if bbox:
        try:
            parts = [float(p) for p in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError()
            # stored as minlat, maxlat, minlon, maxlon for convenience
            bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
            scope = "bbox"
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid bbox format")

    if scope not in ("global", "bbox"):
        raise HTTPException(status_code=400, detail="scope must be 'global' or 'bbox'")

    ds_path = f"{DATA_ROOT}/{RAW_SUBSET}"
    try:
        ds = xr.open_dataset(ds_path, decode_times=False)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {ds_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open dataset: {e}")

    # detect coordinate names and variables
    try:
        lat_name, lon_name = _detect_lat_lon(ds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect coords: {e}")

    # expect variables 'temperature' (anomaly) and 'climatology'
    if "temperature" not in ds.variables or "climatology" not in ds.variables:
        raise HTTPException(
            status_code=500,
            detail="Dataset missing expected variables 'temperature' or 'climatology'",
        )

    time_vals = ds["time"].values.astype(float)

    # build absolute time series (area-weighted) for each time step
    abs_series = []
    for i, tval in enumerate(time_vals):
        month = _month_from_decimal(float(tval))
        # select climatology for month using robust selector
        try:
            clim = _select_climatology_for_month(ds, month)
        except Exception:
            # fallback to naive selection
            try:
                clim = ds["climatology"].isel({ds["climatology"].dims[0]: month - 1})
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed selecting climatology month: {e}"
                )

        temp_anom = ds["temperature"].isel(time=i)
        absolute = clim + temp_anom

        try:
            mean_val = _compute_scope_mean_for_time(
                absolute, lat_name, lon_name, scope, bbox_tuple
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed computing mean: {e}")
        abs_series.append(float(mean_val))

    abs_series = np.array(abs_series, dtype=float)
    # prepare interpolation
    dec_query = _decimal_year_from_date(qdate)

    # guard monotonicity
    sort_idx = np.argsort(time_vals)
    t_sorted = np.array(time_vals)[sort_idx]
    y_sorted = abs_series[sort_idx]

    # interpolation, allow extrapolation by using nearest
    if dec_query <= t_sorted[0]:
        interp_val = float(y_sorted[0])
    elif dec_query >= t_sorted[-1]:
        interp_val = float(y_sorted[-1])
    else:
        interp_val = float(np.interp(dec_query, t_sorted, y_sorted))

    return {"date": qdate.isoformat(), "temperature_c": interp_val}
