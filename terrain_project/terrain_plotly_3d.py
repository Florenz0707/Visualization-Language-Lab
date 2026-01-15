import argparse
import math
import sys

import numpy as np
import plotly.graph_objs as go
import rasterio


def read_raster(fp):
    with rasterio.open(fp) as src:
        print(f"打开: {fp}")
        print(
            f"  CRS: {src.crs}, size: {src.width}x{src.height}, transform: {src.transform}, nodatavals: {src.nodatavals}"
        )
        data = src.read(1).astype(np.float32)
        transform = src.transform
        meta = src.meta.copy()
    # 将 nodata 转为 nan
    nod = meta.get("nodata", None)
    if nod is None:
        # rasterio may not keep nodata in meta
        try:
            with rasterio.open(fp) as s2:
                nod = s2.nodatavals[0]
        except:
            nod = None
    if nod is not None:
        data[data == nod] = np.nan
    return data, transform, meta


# ------------------ 平滑函数（对 NaN 友好，使用可分离一维卷积） ------------------


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
    """对 2D 数组做可分离一维卷积（先行后列），对 NaN 使用掩码分母校正。"""
    if arr.ndim != 2:
        raise ValueError("separable_filter_1d 只支持 2D 数组")
    out = np.empty_like(arr, dtype=np.float64)
    k = kernel

    # first pass: convolve along rows
    for i in range(arr.shape[0]):
        row = arr[i, :]
        mask = np.isfinite(row).astype(np.float64)
        num = np.convolve(np.nan_to_num(row, 0.0), k, mode="same")
        den = np.convolve(mask, k, mode="same")
        with np.errstate(invalid="ignore", divide="ignore"):
            out_row = np.where(den > 0, num / den, np.nan)
        out[i, :] = out_row

    # second pass: convolve along columns
    out2 = np.empty_like(out, dtype=np.float64)
    for j in range(out.shape[1]):
        col = out[:, j]
        mask = np.isfinite(col).astype(np.float64)
        num = np.convolve(np.nan_to_num(col, 0.0), k, mode="same")
        den = np.convolve(mask, k, mode="same")
        with np.errstate(invalid="ignore", divide="ignore"):
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


# ------------------ 结束平滑函数 ------------------


def downsample(arr, factor):
    if factor <= 1:
        return arr
    r = arr.shape[0] // factor
    c = arr.shape[1] // factor
    arrc = arr[: r * factor, : c * factor]
    arr_rs = arrc.reshape(r, factor, c, factor)
    return np.nanmean(arr_rs, axis=(1, 3))


def compute_lonlat(transform, rows, cols):
    # 返回 lon,lat 网格 (rows,cols)
    row_idx = np.arange(rows)
    col_idx = np.arange(cols)
    cols_grid, rows_grid = np.meshgrid(col_idx, row_idx)
    xs, ys = rasterio.transform.xy(transform, rows_grid, cols_grid)
    lon = np.array(xs)
    lat = np.array(ys)
    return lon, lat


def auto_downsample_for_max_verts(shape, max_verts):
    rows, cols = shape
    total = rows * cols
    if total <= max_verts:
        return 1
    factor = math.ceil(math.sqrt(total / max_verts))
    return int(factor)


def meters_to_deg(elev_m, lat_mean):
    # 将米近似转换为度（用于 Z 轴可视化）
    meters_per_deg = 111132.0
    return elev_m / meters_per_deg


def to_chinese_lon_text(vals):
    texts = []
    for v in vals:
        hemi = "东经" if v >= 0 else "西经"
        texts.append(f"{hemi}{abs(v):.2f}°")
    return texts


def to_chinese_lat_text(vals):
    texts = []
    for v in vals:
        hemi = "北纬" if v >= 0 else "南纬"
        texts.append(f"{hemi}{abs(v):.2f}°")
    return texts


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
            i[t] = v0
            j[t] = v2
            k[t] = v1
            t += 1
            i[t] = v1
            j[t] = v2
            k[t] = v3
            t += 1
    mesh = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i.tolist(),
        j=j.tolist(),
        k=k.tolist(),
        intensity=z,
        colorscale="Viridis",
        colorbar=dict(title="Elevation (m)"),
        hoverinfo="skip",
    )
    return mesh


def build_surface(lon, lat, elev):
    surf = go.Surface(
        x=lon,
        y=lat,
        z=elev,
        cmin=float(np.nanpercentile(elev, 1)),
        cmax=float(np.nanpercentile(elev, 99)),
        colorscale="Viridis",
        colorbar=dict(title="Elevation (m)"),
        hovertemplate="Lon: %{x:.4f}<br>Lat: %{y:.4f}<br>Elev: %{z:.2f} m<extra></extra>",
    )
    return surf


def render_3d(lon, lat, elev, out_html, mode="mesh", static=False):
    # prepare axis ticks
    min_lon = float(np.nanmin(lon))
    max_lon = float(np.nanmax(lon))
    min_lat = float(np.nanmin(lat))
    max_lat = float(np.nanmax(lat))
    xvals = np.linspace(min_lon, max_lon, num=6).tolist()
    yvals = np.linspace(min_lat, max_lat, num=6).tolist()
    xtexts = to_chinese_lon_text(xvals)
    ytexts = to_chinese_lat_text(yvals)

    if mode == "mesh":
        print("构建 Mesh3D")
        mesh = build_mesh(lon, lat, elev)
        data = [mesh]
        title = "3D Terrain (Mesh3D)"
    else:
        print("构建 Surface")
        surf = build_surface(lon, lat, elev)
        data = [surf]
        title = "3D Terrain (Surface)"

    # build grid lines at z = min(elev) - small offset
    z0 = float(np.nanmin(elev))
    grid_lines = []
    step_lon = (max_lon - min_lon) / 6.0
    step_lat = (max_lat - min_lat) / 6.0
    for lon_v in np.arange(min_lon, max_lon + 1e-9, step_lon):
        grid_lines.append(
            go.Scatter3d(
                x=[lon_v, lon_v],
                y=[min_lat, max_lat],
                z=[z0 - 1e-6, z0 - 1e-6],
                mode="lines",
                line=dict(color="black", width=1),
                showlegend=False,
                hoverinfo="none",
            )
        )
    for lat_v in np.arange(min_lat, max_lat + 1e-9, step_lat):
        grid_lines.append(
            go.Scatter3d(
                x=[min_lon, max_lon],
                y=[lat_v, lat_v],
                z=[z0 - 1e-6, z0 - 1e-6],
                mode="lines",
                line=dict(color="black", width=1),
                showlegend=False,
                hoverinfo="none",
            )
        )

    data += grid_lines

    layout = go.Layout(
        title=title,
        scene=dict(
            xaxis=dict(title="经度", tickvals=xvals, ticktext=xtexts),
            yaxis=dict(title="纬度", tickvals=yvals, ticktext=ytexts),
            zaxis=dict(title="海拔 (m)"),
            aspectmode="auto",
            camera=dict(
                eye=dict(x=1.0, y=-1.5, z=0.8), projection=dict(type="orthographic")
            ),
        ),
        margin=dict(l=0, r=0, t=30, b=0),
    )

    fig = go.Figure(data=data, layout=layout)
    if static:
        fig.write_html(out_html, include_plotlyjs="cdn", config={"staticPlot": True})
    else:
        fig.write_html(out_html, include_plotlyjs="cdn")
    print(f"写出 HTML: {out_html} (mode={mode}, static={static})")


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(
        "--file",
        type=str,
        required=True,
        help="输入单个 GeoTIFF (DSM) 文件路径，例如 merged_dem_cropped.tif",
    )
    p.add_argument("--out", type=str, default="terrain3d.html", help="输出 HTML 文件")
    p.add_argument(
        "--render",
        type=str,
        default="mesh",
        choices=["mesh", "surface"],
        help="渲染模式：mesh 或 surface",
    )
    p.add_argument("--downsample", type=int, default=1, help="手动下采样因子")
    p.add_argument("--max-verts", type=int, default=150000, help="目标最大顶点数（超出会自动下采样）")
    p.add_argument("--auto-z", action="store_true", help="把米转换为度（近似），使高度在经纬度坐标系下更可见")
    p.add_argument(
        "--z-exag", type=float, default=1.0, help="Z 轴放大倍数（在 auto-z 开启时是额外放大）"
    )
    p.add_argument("--static", action="store_true", help="输出静态 HTML（禁用交互）")
    p.add_argument(
        "--smooth",
        type=str,
        default="none",
        choices=["none", "box", "gaussian"],
        help="是否进行平滑处理（none/box/gaussian）",
    )
    p.add_argument(
        "--smooth-k", type=int, default=3, help="box 平滑时的窗口大小（odd integer, e.g. 3,5,7）"
    )
    p.add_argument(
        "--smooth-sigma", type=float, default=1.0, help="gaussian 平滑时的 sigma（像素单位）"
    )
    args = p.parse_args(argv)

    data, transform, meta = read_raster(args.file)
    print("原始形状:", data.shape)

    # 平滑（在下采样前进行以避免别名）
    if args.smooth != "none":
        print(f"开始平滑：mode={args.smooth}")
        if args.smooth == "box":
            k = max(1, args.smooth_k)
            if k % 2 == 0:
                print("警告?：建议使用奇数窗口大小，已自动加 1")
                k += 1
            data = smooth_box(data, k)
            print(f"box 平滑完成，窗口大小={k}")
        else:
            sigma = max(0.0, float(args.smooth_sigma))
            data = smooth_gaussian(data, sigma)
            print(f"gaussian 平滑完成，sigma={sigma}")

    # 自动下采样判断
    if args.downsample <= 1:
        factor = auto_downsample_for_max_verts(data.shape, args.max_verts)
        if factor > 1:
            print(f"自动下采样因子: {factor}（以满足 max_verts={args.max_verts}）")
            args.downsample = factor

    if args.downsample > 1:
        data = downsample(data, args.downsample)
        transform = rasterio.Affine(
            transform.a * args.downsample,
            transform.b,
            transform.c,
            transform.d,
            transform.e * args.downsample,
            transform.f,
        )
        print("下采样后形状:", data.shape)

    lon, lat = compute_lonlat(transform, data.shape[0], data.shape[1])

    # 处理 nodata
    if not np.isfinite(data).any():
        print("ERROR: 读到的数据无有效值，退出")
        sys.exit(1)

    elev = data
    if args.auto_z:
        lat_mean = float(np.nanmean(lat))
        elev_deg = meters_to_deg(elev, lat_mean) * args.z_exag
        print(f"启用 auto-z：将海拔(m) 转换为度，mean_lat={lat_mean:.4f}，并乘以 z-exag={args.z_exag}")
        elev_plot = elev_deg
    else:
        elev_plot = elev * args.z_exag

    render_3d(lon, lat, elev_plot, args.out, mode=args.render, static=args.static)


if __name__ == "__main__":
    main(sys.argv[1:])
