#!/usr/bin/env python3
# terrain_plotly_3d_with_vectors_fixed.py
"""
3D Terrain visualization (Plotly) with vector overlays (countries, admin1, cities, rivers).
Includes smoothing (box / gaussian), auto downsample, auto-z conversion (m -> deg), and robust lon/lat handling.

Save as: terrain_plotly_3d_with_vectors_fixed.py
Dependencies (recommended via conda-forge):
  conda install -c conda-forge rasterio geopandas plotly shapely fiona pyproj rtree

Or pip (may be harder for geopandas-related C deps):
  pip install rasterio plotly shapely fiona pyproj geopandas
"""

import argparse
import math
import sys
import numpy as np
import rasterio
import geopandas as gpd
import shapely.geometry as geom
import plotly.graph_objs as go

# ------------------ raster helpers ------------------

def read_raster(fp):
    with rasterio.open(fp) as src:
        print(f"打开: {fp}")
        print(f"  CRS: {src.crs}, size: {src.width}x{src.height}, transform: {src.transform}, nodatavals: {src.nodatavals}")
        data = src.read(1).astype(np.float32)
        transform = src.transform
        meta = src.meta.copy()
        nod = src.nodatavals[0] if src.nodatavals else None
        # store nodata in meta if present
        if nod is not None:
            meta['nodata'] = nod
    # 将 nodata 转为 nan
    if 'nodata' in meta and meta['nodata'] is not None:
        nod = meta['nodata']
        data[data == nod] = np.nan
    return data, transform, meta

def downsample(arr, factor):
    if factor <= 1:
        return arr
    r = arr.shape[0] // factor
    c = arr.shape[1] // factor
    arrc = arr[: r * factor, : c * factor]
    arr_rs = arrc.reshape(r, factor, c, factor)
    return np.nanmean(arr_rs, axis=(1, 3))

# Robust compute_lonlat: always returns 2D lon_grid, lat_grid (rows, cols)
def compute_lonlat(transform, rows, cols):
    """
    Compute lon/lat 2D grids referencing pixel centers using Affine transform.
    Returns lon_grid, lat_grid shaped (rows, cols).
    """
    a = float(transform.a)  # pixel width
    c = float(transform.c)  # x origin
    e = float(transform.e)  # pixel height (often negative)
    f = float(transform.f)  # y origin

    cols_idx = np.arange(cols, dtype=np.float64)
    rows_idx = np.arange(rows, dtype=np.float64)
    # pixel center coordinates
    lon_1d = c + (cols_idx + 0.5) * a
    lat_1d = f + (rows_idx + 0.5) * e
    lon_grid, lat_grid = np.meshgrid(lon_1d, lat_1d)
    return lon_grid, lat_grid

def auto_downsample_for_max_verts(shape, max_verts):
    rows, cols = shape
    total = rows * cols
    if total <= max_verts:
        return 1
    factor = math.ceil(math.sqrt(total / max_verts))
    return int(factor)

def meters_to_deg(elev_m, lat_mean):
    meters_per_deg = 111132.0
    return elev_m / meters_per_deg

# ------------------ smoothing (NaN-aware separable convolution) ------------------

def gaussian_kernel_1d(sigma: float):
    if sigma <= 0:
        return np.array([1.0], dtype=np.float64)
    radius = max(1, int(3.0 * sigma))
    x = np.arange(-radius, radius + 1)
    k = np.exp(-0.5 * (x / float(sigma)) ** 2)
    k = k / k.sum()
    return k.astype(np.float64)

def box_kernel_1d(k: int):
    if k <= 1:
        return np.array([1.0], dtype=np.float64)
    arr = np.ones(k, dtype=np.float64)
    arr = arr / arr.sum()
    return arr

def separable_filter_1d(arr: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    if arr.ndim != 2:
        raise ValueError("separable_filter_1d only supports 2D arrays")
    out = np.empty_like(arr, dtype=np.float64)
    k = kernel
    # rows
    for i in range(arr.shape[0]):
        row = arr[i, :]
        mask = np.isfinite(row).astype(np.float64)
        num = np.convolve(np.nan_to_num(row, 0.0), k, mode='same')
        den = np.convolve(mask, k, mode='same')
        with np.errstate(invalid='ignore', divide='ignore'):
            out_row = np.where(den > 0, num / den, np.nan)
        out[i, :] = out_row
    # cols
    out2 = np.empty_like(out, dtype=np.float64)
    for j in range(out.shape[1]):
        col = out[:, j]
        mask = np.isfinite(col).astype(np.float64)
        num = np.convolve(np.nan_to_num(col, 0.0), k, mode='same')
        den = np.convolve(mask, k, mode='same')
        with np.errstate(invalid='ignore', divide='ignore'):
            out_col = np.where(den > 0, num / den, np.nan)
        out2[:, j] = out_col
    return out2.astype(arr.dtype)

def smooth_box(arr: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return arr
    kernel = box_kernel_1d(k)
    return separable_filter_1d(arr, kernel)

def smooth_gaussian(arr: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return arr
    kernel = gaussian_kernel_1d(sigma)
    return separable_filter_1d(arr, kernel)

# ------------------ shapefile utilities ------------------

def load_shapefile(fp, simplify_tol=0.01):
    if not fp:
        return None
    print(f"读取矢量: {fp}")
    g = gpd.read_file(fp)
    if g.crs is None:
        print(f"  警告：{fp} 无 CRS 信息，假定 EPSG:4326")
        g = g.set_crs(epsg=4326)
    if g.crs.to_string() != 'EPSG:4326':
        g = g.to_crs(epsg=4326)
    if simplify_tol and simplify_tol > 0:
        print(f"  简化几何 (tol={simplify_tol}) ...")
        g['geometry'] = g['geometry'].simplify(simplify_tol, preserve_topology=True)
    return g

def sample_elev_nearest(lon_1d, lat_1d, elev_grid, x, y):
    if np.isnan(x) or np.isnan(y):
        return np.nan
    # ensure lon_1d / lat_1d are 1D
    lon_arr = np.asarray(lon_1d).ravel()
    lat_arr = np.asarray(lat_1d).ravel()
    col = int(np.abs(lon_arr - x).argmin())
    row = int(np.abs(lat_arr - y).argmin())
    if 0 <= row < elev_grid.shape[0] and 0 <= col < elev_grid.shape[1]:
        return float(elev_grid[row, col])
    return np.nan

def geometry_to_3d_coords(geom_obj, lon_1d, lat_1d, elev_grid, max_points=5000, z_offset=0.0):
    xs_all = []; ys_all = []; zs_all = []
    def append_coords(xs, ys, zs):
        xs_all.extend(xs); ys_all.extend(ys); zs_all.extend(zs)
        xs_all.append(None); ys_all.append(None); zs_all.append(None)
    def process_coords(coords):
        n = len(coords)
        if n == 0:
            return [], [], []
        step = max(1, int(math.ceil(n / max_points)))
        coords_sub = coords[::step]
        xs = [c[0] for c in coords_sub]
        ys = [c[1] for c in coords_sub]
        zs = []
        for xi, yi in zip(xs, ys):
            z = sample_elev_nearest(lon_1d, lat_1d, elev_grid, xi, yi)
            if np.isnan(z):
                zs.append(np.nan)
            else:
                zs.append(z + z_offset)
        return xs, ys, zs
    if geom_obj is None:
        return [], [], []
    gtype = geom_obj.geom_type
    if gtype == 'LineString' or gtype == 'LinearRing':
        xs, ys, zs = process_coords(list(geom_obj.coords)); append_coords(xs, ys, zs)
    elif gtype == 'Polygon':
        ext = geom_obj.exterior; xs, ys, zs = process_coords(list(ext.coords)); append_coords(xs, ys, zs)
        for interior in geom_obj.interiors:
            xs, ys, zs = process_coords(list(interior.coords)); append_coords(xs, ys, zs)
    elif gtype.startswith('Multi') or gtype == 'GeometryCollection':
        for part in geom_obj.geoms:
            xsub, ysub, zsub = geometry_to_3d_coords(part, lon_1d, lat_1d, elev_grid, max_points=max_points, z_offset=z_offset)
            if xsub:
                xs_all.extend(xsub); ys_all.extend(ysub); zs_all.extend(zsub)
    else:
        try:
            coords = list(geom_obj.coords)
            xs, ys, zs = process_coords(coords); append_coords(xs, ys, zs)
        except Exception:
            pass
    return xs_all, ys_all, zs_all

# ------------------ plotting ------------------

def build_mesh(lon, lat, elev):
    rows, cols = elev.shape
    x = lon.ravel().astype(np.float32)
    y = lat.ravel().astype(np.float32)
    z = elev.ravel().astype(np.float32)
    tri_count = 2 * (rows - 1) * (cols - 1)
    i = np.empty(tri_count, dtype=np.int32)
    j = np.empty(tri_count, dtype=np.int32)
    k = np.empty(tri_count, dtype=np.int32)
    t = 0
    for r in range(rows - 1):
        for c in range(cols - 1):
            v0 = r * cols + c
            v1 = v0 + 1
            v2 = v0 + cols
            v3 = v2 + 1
            i[t] = v0; j[t] = v2; k[t] = v1; t += 1
            i[t] = v1; j[t] = v2; k[t] = v3; t += 1
    mesh = go.Mesh3d(x=x, y=y, z=z, i=i.tolist(), j=j.tolist(), k=k.tolist(), intensity=z,
                     colorscale='Viridis', colorbar=dict(title='Elevation (m)'), hoverinfo='skip', name='Terrain')
    return mesh

def build_surface(lon, lat, elev):
    surf = go.Surface(x=lon, y=lat, z=elev, cmin=float(np.nanpercentile(elev, 1)),
                      cmax=float(np.nanpercentile(elev, 99)), colorscale='Viridis',
                      colorbar=dict(title='Elevation (m)'), hovertemplate='Lon: %{x:.4f}<br>Lat: %{y:.4f}<br>Elev: %{z:.2f} m<extra></extra>',
                      name='Terrain')
    return surf

def to_chinese_lon_text(vals):
    texts = []
    for v in vals:
        hemi = '东经' if v >= 0 else '西经'
        texts.append(f"{hemi}{abs(v):.2f}°")
    return texts

def to_chinese_lat_text(vals):
    texts = []
    for v in vals:
        hemi = '北纬' if v >= 0 else '南纬'
        texts.append(f"{hemi}{abs(v):.2f}°")
    return texts

def render_3d_with_vectors(lon, lat, elev_plot, out_html, mode='mesh', static=False,
                           g_countries=None, g_admin1=None, g_cities=None, g_rivers=None,
                           simplify_tol=0.01):
    min_lon = float(np.nanmin(lon)); max_lon = float(np.nanmax(lon))
    min_lat = float(np.nanmin(lat)); max_lat = float(np.nanmax(lat))
    xvals = np.linspace(min_lon, max_lon, num=6).tolist()
    yvals = np.linspace(min_lat, max_lat, num=6).tolist()
    xtexts = to_chinese_lon_text(xvals)
    ytexts = to_chinese_lat_text(yvals)

    terrain = build_mesh(lon, lat, elev_plot) if mode == 'mesh' else build_surface(lon, lat, elev_plot)
    data = [terrain]

    # robustly get 1D lon/lat for sampling:
    if lon.ndim == 2:
        lon_1d = lon[0, :].astype(np.float64)
    else:
        lon_1d = lon.astype(np.float64)
    if lat.ndim == 2:
        lat_1d = lat[:, 0].astype(np.float64)
    else:
        lat_1d = lat.astype(np.float64)

    elev_range = np.nanmax(elev_plot) - np.nanmin(elev_plot) if np.isfinite(elev_plot).any() else 1.0
    z_offset = max(elev_range * 0.001, 1e-6)

    # Countries
    if g_countries is not None and len(g_countries) > 0:
        print('添加国家边界...')
        xs, ys, zs = [], [], []
        for geom1 in g_countries.geometry:
            xsub, ysub, zsub = geometry_to_3d_coords(geom1, lon_1d, lat_1d, elev_plot, max_points=3000, z_offset=z_offset)
            if xsub:
                xs.extend(xsub); ys.extend(ysub); zs.extend(zsub)
        if xs:
            data.append(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='black', width=2), name='Countries'))

    # Admin1
    if g_admin1 is not None and len(g_admin1) > 0:
        print('添加一级行政区...')
        xs, ys, zs = [], [], []
        for geom1 in g_admin1.geometry:
            xsub, ysub, zsub = geometry_to_3d_coords(geom1, lon_1d, lat_1d, elev_plot, max_points=2000, z_offset=z_offset*1.2)
            if xsub:
                xs.extend(xsub); ys.extend(ysub); zs.extend(zsub)
        if xs:
            data.append(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='orange', width=1), name='Admin1'))

    # Rivers
    if g_rivers is not None and len(g_rivers) > 0:
        print('添加河流...')
        xs, ys, zs = [], [], []
        for geom1 in g_rivers.geometry:
            xsub, ysub, zsub = geometry_to_3d_coords(geom1, lon_1d, lat_1d, elev_plot, max_points=2000, z_offset=z_offset*1.5)
            if xsub:
                xs.extend(xsub); ys.extend(ysub); zs.extend(zsub)
        if xs:
            data.append(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='blue', width=1), name='Rivers'))

    # Cities
    if g_cities is not None and len(g_cities) > 0:
        print('添加城市点...')
        cx = []; cy = []; cz = []; text = []; sizes = []
        for idx, row in g_cities.iterrows():
            pt = row.geometry
            if pt is None or pt.is_empty:
                continue
            lon_p = float(pt.x); lat_p = float(pt.y)
            elev_pt = sample_elev_nearest(lon_1d, lat_1d, elev_plot, lon_p, lat_p)
            if np.isnan(elev_pt):
                continue
            cz.append(elev_pt + z_offset * 3.0)
            cx.append(lon_p); cy.append(lat_p)
            name = row.get('NAME', row.get('name', row.get('NAME_EN', '')))
            pop = row.get('POP_MAX', row.get('POP', row.get('population', None)))
            txt = f"{name}<br>POP: {pop}" if pop is not None else f"{name}"
            text.append(txt)
            if pop is None or not np.isfinite(pop):
                sizes.append(3)
            else:
                sizes.append(max(3, min(12, math.log10(max(1, float(pop))) * 1.8)))
        if cx:
            data.append(go.Scatter3d(x=cx, y=cy, z=cz, mode='markers', marker=dict(size=sizes, color='red', opacity=0.8), hovertext=text, hoverinfo='text', name='Cities'))

    layout = go.Layout(
        title='3D Terrain with Boundaries',
        scene=dict(
            xaxis=dict(title='经度', tickvals=xvals, ticktext=xtexts),
            yaxis=dict(title='纬度', tickvals=yvals, ticktext=ytexts),
            zaxis=dict(title='海拔 (m)'),
            aspectmode='auto',
            camera=dict(eye=dict(x=1.0, y=-1.5, z=0.8), projection=dict(type='orthographic'))
        ),
        margin=dict(l=0, r=0, t=30, b=0)
    )

    fig = go.Figure(data=data, layout=layout)
    if static:
        fig.write_html(out_html, include_plotlyjs='cdn', config={'staticPlot': True})
    else:
        fig.write_html(out_html, include_plotlyjs='cdn')
    print(f"写出 HTML: {out_html} (mode={mode}, static={static})")

# ------------------ CLI main ------------------

def main(argv):
    p = argparse.ArgumentParser(description='3D Terrain + Vector Overlays (fixed lon/lat handling)')
    p.add_argument('--file', type=str, required=True, help='输入 GeoTIFF (DSM)（例如 merged_dem_cropped.tif）')
    p.add_argument('--out', type=str, default='terrain3d_with_vectors.html', help='输出 HTML 文件')
    p.add_argument('--render', type=str, default='mesh', choices=['mesh','surface'], help='渲染模式：mesh 或 surface')
    p.add_argument('--downsample', type=int, default=1, help='下采样因子')
    p.add_argument('--max-verts', type=int, default=120000, help='目标最大顶点数（超出会自动下采样）')
    p.add_argument('--auto-z', action='store_true', help='把米转换为度（近似）')
    p.add_argument('--z-exag', type=float, default=1.0, help='Z 轴放大倍数（在 auto-z 开启时为额外放大）')
    p.add_argument('--static', action='store_true', help='输出静态 HTML（禁用交互）')
    p.add_argument('--countries', type=str, default=r"F:/Professional_books/visualization/project/Visualization-Language-Lab/terrain_project/public/data/boundaries/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp", help='admin_0 shapefile')
    p.add_argument('--admin1', type=str, default=r"F:/Professional_books/visualization/project/Visualization-Language-Lab/terrain_project/public/data/boundaries/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp", help='admin_1 shapefile')
    p.add_argument('--cities', type=str, default=r"F:/Professional_books/visualization/project/Visualization-Language-Lab/terrain_project/public/data/boundaries/ne_10m_populated_places/ne_10m_populated_places.shp", help='populated places shapefile')
    p.add_argument('--rivers', type=str, default=r"F:/Professional_books/visualization/project/Visualization-Language-Lab/terrain_project/public/data/boundaries/ne_10m_rivers_lake_centerlines/ne_10m_rivers_lake_centerlines.shp", help='rivers shapefile')
    p.add_argument('--simplify-tol', type=float, default=0.01, help='几何简化容差（度）')
    p.add_argument('--smooth', type=str, default='none', choices=['none','box','gaussian'], help='是否进行平滑处理')
    p.add_argument('--smooth-k', type=int, default=3, help='box 平滑窗口大小（奇数）')
    p.add_argument('--smooth-sigma', type=float, default=1.0, help='gaussian sigma（像素单位）')
    args = p.parse_args(argv)

    data, transform, meta = read_raster(args.file)
    print('原始形状:', data.shape)

    # smoothing
    if args.smooth != 'none':
        print(f"开始平滑：mode={args.smooth}")
        if args.smooth == 'box':
            k = max(1, args.smooth_k)
            if k % 2 == 0:
                print("警告：建议使用奇数窗口大小，已自动加 1")
                k += 1
            data = smooth_box(data, k)
            print(f"box 平滑完成，窗口大小={k}")
        else:
            sigma = max(0.0, float(args.smooth_sigma))
            data = smooth_gaussian(data, sigma)
            print(f"gaussian 平滑完成，sigma={sigma}")

    # auto downsample
    if args.downsample <= 1:
        factor = auto_downsample_for_max_verts(data.shape, args.max_verts)
        if factor > 1:
            print(f"自动下采样因子: {factor}（以满足 max_verts={args.max_verts}）")
            args.downsample = factor

    if args.downsample > 1:
        data = downsample(data, args.downsample)
        transform = rasterio.Affine(transform.a * args.downsample, transform.b, transform.c, transform.d, transform.e * args.downsample, transform.f)
        print('下采样后形状:', data.shape)

    lon, lat = compute_lonlat(transform, data.shape[0], data.shape[1])
    print("lon shape:", getattr(lon, "shape", None), "lat shape:", getattr(lat, "shape", None))

    if not np.isfinite(data).any():
        print('ERROR: 读到的数据无有效值，退出'); sys.exit(1)

    elev = data
    if args.auto_z:
        lat_mean = float(np.nanmean(lat))
        elev_deg = meters_to_deg(elev, lat_mean) * args.z_exag
        print(f"启用 auto-z：mean_lat={lat_mean:.4f}, z-exag={args.z_exag}")
        elev_plot = elev_deg
    else:
        elev_plot = elev * args.z_exag

    # load shapefiles
    g_countries = load_shapefile(args.countries, simplify_tol=args.simplify_tol) if args.countries else None
    g_admin1 = load_shapefile(args.admin1, simplify_tol=args.simplify_tol) if args.admin1 else None
    g_cities = load_shapefile(args.cities, simplify_tol=args.simplify_tol) if args.cities else None
    g_rivers = load_shapefile(args.rivers, simplify_tol=args.simplify_tol) if args.rivers else None

    render_3d_with_vectors(lon, lat, elev_plot, args.out, mode=args.render, static=args.static,
                           g_countries=g_countries, g_admin1=g_admin1, g_cities=g_cities, g_rivers=g_rivers,
                           simplify_tol=args.simplify_tol)

if __name__ == '__main__':
    main(sys.argv[1:])
