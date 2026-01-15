from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

p = Path("data/noaa/berkeley/Raw_TAVG_1750_1850.nc")
ds = xr.open_dataset(p)
# 目标 decimal-year 值（示例取 1812.0416667）
target = 1812.0416666666667
# 找到最接近的 time 索引
time_vals = ds["time"].values.astype(float)
tidx = int(np.abs(time_vals - target).argmin())
tval = float(time_vals[tidx])
print("chosen time index, value:", tidx, tval)

# 将 decimal-year 转成月份（mid-month scheme）
year = np.floor(tval).astype(int)
frac = tval - year
month = int(np.clip((frac * 12 + 0.5).astype(int), 1, 12))
print("mapped to month:", month)

# 取异常场和对应的基线月场
anomaly = ds["temperature"].isel(time=tidx)  # (lat, lon) or (map_points)
clim = ds["climatology"].sel(month_number=month)  # (month_number,lat,lon) -> (lat,lon)

# 若 climatology 与 anomaly 维度命名不同（map_points），对齐
clim_aligned = clim
if set(clim.dims) != set(anomaly.dims):
    clim_aligned = clim.transpose(*anomaly.dims)

absolute = clim_aligned + anomaly
# 输出：全局加权平均（按纬度权重）
lat_dim = next((n for n in ds.coords if n.lower().startswith("lat")), None)
lon_dim = next((n for n in ds.coords if n.lower().startswith("lon")), None)
if lat_dim and lon_dim:
    weights = np.cos(np.deg2rad(ds[lat_dim]))
    # if weights is 1D, broadcast; xarray handles broadcasting in weighted()
    gmean = absolute.weighted(weights).mean((lat_dim, lon_dim))
    out_csv = Path("data/noaa/berkeley/absolute_temperature_{}_global.csv".format(year))
    # if gmean is scalar, write single-row CSV; otherwise convert to DataFrame
    try:
        if getattr(gmean, "ndim", 0) == 0:
            # map decimal-year to ISO mid-month date
            t = tval
            y = int(np.floor(t))
            m = int(np.clip((t - y) * 12 + 0.5, 1, 12))
            date = pd.Timestamp(year=y, month=m, day=15).strftime("%Y-%m-%d")
            out_df = pd.DataFrame({"date": [date], "tavg_abs": [float(gmean.values)]})
            out_df.to_csv(out_csv, index=False)
        else:
            gmean.to_dataframe(name="tavg_abs").to_csv(out_csv)
        print("Wrote global mean CSV:", out_csv)
    except Exception:
        # fallback: write scalar
        try:
            val = float(gmean.values)
            pd.DataFrame({"tavg_abs": [val]}).to_csv(out_csv, index=False)
            print("Wrote global mean CSV (fallback):", out_csv)
        except Exception as e:
            print("Failed to write global mean CSV:", e)
else:
    print("No lat/lon dims found — grid may be map_points. Saving sample stats.")
    # save mean over available dims
    m = absolute.mean()
    print(m.values)

# 如果需要 DEM bbox 内的平均，请指定 bbox（示例用项目 DEM bbox）
dem_bbox = (50, 60, 20, 45)  # (minLat,maxLat,minLon,maxLon)
# 子集并计算区域平均（仅当有 lat/lon dims）
if lat_dim and lon_dim:
    sub = absolute.sel(
        {
            lat_dim: slice(dem_bbox[0], dem_bbox[1]),
            lon_dim: slice(dem_bbox[2], dem_bbox[3]),
        }
    )
    # area-weighted mean within bbox
    w = np.cos(np.deg2rad(sub[lat_dim]))
    rb = sub.weighted(w).mean((lat_dim, lon_dim))
    out_bbox = Path(
        "data/noaa/berkeley/absolute_temperature_{}_bbox_mean.csv".format(year)
    )
    try:
        if getattr(rb, "ndim", 0) == 0:
            # same date mapping as above
            t = tval
            y = int(np.floor(t))
            m = int(np.clip((t - y) * 12 + 0.5, 1, 12))
            date = pd.Timestamp(year=y, month=m, day=15).strftime("%Y-%m-%d")
            pd.DataFrame({"date": [date], "tavg_abs_bbox": [float(rb.values)]}).to_csv(
                out_bbox, index=False
            )
        else:
            rb.to_dataframe(name="tavg_abs_bbox").to_csv(out_bbox)
        print("Wrote bbox mean CSV:", out_bbox)
    except Exception as e:
        print("Failed to write bbox mean CSV:", e)
else:
    print("Cannot compute bbox mean without lat/lon dims.")
