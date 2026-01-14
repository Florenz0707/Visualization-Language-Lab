#!/usr/bin/env python3
"""Download Berkeley Earth gridded data and extract year 1812 over DEM bbox.

Behavior:
- Scrapes https://berkeleyearth.org/data/ for available .nc files and selects
  a land or land+ocean gridded NetCDF.
- Downloads the file to `data/noaa/berkeley/`.
- If `xarray` is installed, opens the file, selects year 1812 and the bbox
  computed from `data/dem/jaxa_aw3d30` tiles, and writes a small subset netcdf
  and CSV with monthly values.

Usage:
  python3 scripts/download_berkeley_1812.py

Note: `xarray` and `netcdf4` are optional but recommended for subsetting.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

import requests

# Use a browser-like User-Agent to avoid 403 from some hosts
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


ROOT = Path(__file__).resolve().parents[1]
DEM_DIR = ROOT / "data" / "dem" / "jaxa_aw3d30"
OUT_DIR = ROOT / "data" / "noaa" / "berkeley"


def parse_tile_name(name: str) -> Tuple[float, float, float, float]:
    m = re.match(r"([NS])(\d{2,3})([EW])(\d{2,3})_([NS])(\d{2,3})([EW])(\d{2,3})", name)
    if not m:
        raise ValueError(name)
    lat1 = int(m.group(2)) * (1 if m.group(1) == "N" else -1)
    lon1 = int(m.group(4)) * (1 if m.group(3) == "E" else -1)
    lat2 = int(m.group(6)) * (1 if m.group(5) == "N" else -1)
    lon2 = int(m.group(8)) * (1 if m.group(7) == "E" else -1)
    return min(lat1, lat2), max(lat1, lat2), min(lon1, lon2), max(lon1, lon2)


def compute_bbox_from_dem(dem_dir: Path) -> Tuple[float, float, float, float]:
    names = [p.name for p in dem_dir.iterdir() if p.is_dir()]
    if not names:
        raise RuntimeError(f"No tiles in {dem_dir}")
    lat_mins, lat_maxs, lon_mins, lon_maxs = [], [], [], []
    for n in names:
        a, b, c, d = parse_tile_name(n)
        lat_mins.append(a)
        lat_maxs.append(b)
        lon_mins.append(c)
        lon_maxs.append(d)
    return min(lat_mins), max(lat_maxs), min(lon_mins), max(lon_maxs)


def find_nc_link() -> Optional[str]:
    url = "https://berkeleyearth.org/data/"
    r = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
    r.raise_for_status()
    html = r.text
    # find all hrefs ending with .nc
    hrefs = re.findall(r'href=["\']([^"\']+\.nc)["\']', html)
    # prefer links with 'Land' or 'land' or 'LatLong'
    candidates = [h for h in hrefs if re.search(r"land|Land|LatLong|gridded|Grid", h)]
    if not candidates:
        candidates = hrefs
    if not candidates:
        return None
    # normalize relative urls
    for c in candidates:
        if c.startswith("http"):
            return c
    # pick first and join with site
    return requests.compat.urljoin(url, candidates[0])


def download_file(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {out_path}")
    sess = requests.Session()
    sess.headers.update(BROWSER_HEADERS)
    with sess.get(url, stream=True, timeout=60, allow_redirects=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)


def subset_and_save(
    nc_path: Path, bbox: Tuple[float, float, float, float], year: int = 1812
) -> None:
    try:
        import xarray as xr
    except Exception:
        print(
            "xarray not installed; skipping subsetting. Install xarray and netCDF4 to enable this."
        )
        return
    ds = xr.open_dataset(nc_path)
    # Heuristics: try common coord names
    lat_name = next((n for n in ds.coords if n.lower().startswith("lat")), None)
    lon_name = next((n for n in ds.coords if n.lower().startswith("lon")), None)
    time_name = next((n for n in ds.coords if n.lower().startswith("time")), None)
    if not (lat_name and lon_name and time_name):
        print("Could not detect lat/lon/time coords in dataset; aborting subsetting")
        return
    # handle 1D lat/lon vs 2D grid coords
    lat_coord = ds.coords[lat_name]
    lon_coord = ds.coords[lon_name]
    # If lat/lon are 1D coordinates that are also dataset dimensions, use .sel with slices.
    is_1d_index = (
        getattr(lat_coord, "ndim", 1) == 1
        and getattr(lon_coord, "ndim", 1) == 1
        and lat_name in ds.dims
        and lon_name in ds.dims
    )
    if is_1d_index:
        ds_sub = ds.sel(
            {lat_name: slice(bbox[0], bbox[1]), lon_name: slice(bbox[2], bbox[3])}
        )
    else:
        # 2D or non-dimension coordinates (curvilinear grid): build boolean mask
        # broadcast lat/lon to a common shape if needed
        try:
            lat_arr = lat_coord
            lon_arr = lon_coord
            # ensure same shape
            if lat_arr.shape != lon_arr.shape:
                lat_arr, lon_arr = xr.broadcast(lat_arr, lon_arr)
            mask = (
                (lat_arr >= bbox[0])
                & (lat_arr <= bbox[1])
                & (lon_arr >= bbox[2])
                & (lon_arr <= bbox[3])
            )
            ds_sub = ds.where(mask, drop=True)
        except Exception as e:
            print("Failed to build mask for curvilinear grid:", e)
            return
    # select year from time using slice to avoid index-grouping KeyError
    try:
        ds_time = ds_sub.sel({time_name: slice(f"{year}-01-01", f"{year}-12-31")})
    except Exception:
        # fallback: use explicit indexing via pandas
        import numpy as _np
        import pandas as _pd

        times = ds_sub[time_name].values
        try:
            yrs = _pd.DatetimeIndex(times).year
            idx = _np.nonzero(yrs == year)[0]
            if idx.size == 0:
                print(f"No data for year {year} after subsetting")
                return
            ds_time = ds_sub.isel({time_name: idx})
        except Exception as e:
            print("Failed to index time coordinate:", e)
            return
    out_nc = nc_path.with_name(nc_path.stem + f"_yr{year}.nc")
    ds_time.to_netcdf(out_nc)
    print(f"Wrote subset NetCDF to {out_nc}")
    # also write CSV of monthly mean per cell (lat,lon,value,time)
    try:
        df = ds_time.to_dataframe().reset_index()
        csv_out = out_nc.with_suffix(".csv")
        df.to_csv(csv_out, index=False)
        print(f"Wrote CSV to {csv_out}")
    except Exception as e:
        print("Failed to write CSV:", e)


def main() -> int:
    print("Computing DEM bbox...")
    bbox = compute_bbox_from_dem(DEM_DIR)
    print(f"bbox: {bbox}")
    link = find_nc_link()
    if not link:
        print(
            "Could not find NetCDF link on Berkeley Earth data page. Please download manually."
        )
        return 2
    out_file = OUT_DIR / Path(link).name
    if not out_file.exists():
        download_file(link, out_file)
    else:
        print(f"{out_file} already exists; skipping download")
    subset_and_save(out_file, bbox, year=1812)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
