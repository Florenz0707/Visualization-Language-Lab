"""
生成历史事件的控制区域 GeoJSON 文件
基于 events.geojson，按指定缓冲半径和时间窗口生成各阵营的控制区域
"""


import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "data" / "geojson" / "events.geojson"
OUT = ROOT / "data" / "geojson" / "territories.geojson"

# parameters
buffer_km = 50  # 缓冲半径，单位 km
time_window = ("1812-06-24", "1812-12-14")  # 可改为按窗口生成多时刻快照


def parse_date(s):
    try:
        return datetime.fromisoformat(s).date()
    except:
        return None


def main():
    # read raw geojson to preserve original 'properties' dicts
    with open(IN, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    g = gpd.read_file(IN)
    # ensure a 'properties' column exists (GeoPandas usually expands properties into columns)
    if "properties" not in g.columns:
        props = [f.get("properties", {}) for f in raw.get("features", [])]
        g["properties"] = props
    # 过滤时间窗口（可选）
    start, end = map(datetime.fromisoformat, time_window)
    g["date_parsed"] = g["properties"].apply(
        lambda p: parse_date(p.get("date") if isinstance(p, dict) else None)
    )
    g = g[(g["date_parsed"] >= start.date()) & (g["date_parsed"] <= end.date())]

    # 选择需要作为“控制”判断的属性 (示例：faction 或 根据有兵力字段判定)
    def faction_of(props):
        if not isinstance(props, dict):
            return None
        if props.get("french_troops") is not None or any(
            "Napoleon" in c for c in (props.get("french_commanders") or [])
        ):
            return "french"
        if props.get("austrian_troops") is not None or str(
            props.get("id", "")
        ).startswith("evt_sch_"):
            return "austrian"
        return props.get("faction") or "other"

    g["faction"] = g["properties"].apply(faction_of)

    # 投影到米制（WebMercator），以 km 为单位缓冲
    g = g.to_crs(epsg=3857)
    g["geom_buf"] = g.geometry.buffer(buffer_km * 1000)

    # 按 faction 溶解
    out_feats = []
    for fac, grp in g.groupby("faction"):
        polys = list(grp["geom_buf"].values)
        union = unary_union(polys)
        out_feats.append(
            {"geometry": union, "properties": {"faction": fac, "count": len(grp)}}
        )

    # build GeoDataFrame from geometries and properties
    geoms = [f["geometry"] for f in out_feats]
    props = [f["properties"] for f in out_feats]
    out_gdf = gpd.GeoDataFrame(props, geometry=geoms, crs="EPSG:3857")
    out_gdf = out_gdf.to_crs(epsg=4326)
    out_gdf.to_file(OUT, driver="GeoJSON")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
