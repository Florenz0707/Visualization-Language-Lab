import json
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.windows import Window
from PIL import Image
from shapely.geometry import LineString, Point
import pandas as pd
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# ================= 1. 配置路径 =================
# 自动获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_JSON = os.path.join(BASE_DIR, "game_data.json")
OUTPUT_HEIGHTMAP = os.path.join(ASSETS_DIR, "heightmap.png")

# 确保输出目录存在
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

PATH_DEM = os.path.join(DATA_DIR, "dem.tif")
PATH_CITIES = os.path.join(DATA_DIR, "cities.geojson")
PATH_RIVERS = os.path.join(DATA_DIR, "rivers.geojson")
PATH_EVENTS = os.path.join(DATA_DIR, "events.geojson")

# ================= 2. 地图参数 =================
# 请确保这个范围覆盖了你的 events 和 dem
BOUNDS = {
    'min_lon': 20.0, 'max_lon': 45.0,
    'min_lat': 50.0, 'max_lat': 60.0
}

WORLD_WIDTH = 250
WORLD_HEIGHT = 100
DEM_MIN = 0
DEM_MAX = 1000

def map_coords(lon, lat):
    """将经纬度转为 Three.js (x, z)"""
    nx = (lon - BOUNDS['min_lon']) / (BOUNDS['max_lon'] - BOUNDS['min_lon'])
    ny = (lat - BOUNDS['min_lat']) / (BOUNDS['max_lat'] - BOUNDS['min_lat'])
    wx = (nx - 0.5) * WORLD_WIDTH
    wz = -(ny - 0.5) * WORLD_HEIGHT 
    return round(wx, 3), round(wz, 3)

def get_height_normalized(lon, lat, dem_src):
    """从 DEM 采样高度并归一化 (0-1)"""
    try:
        row, col = dem_src.index(lon, lat)
        if row < 0 or col < 0 or row >= dem_src.height or col >= dem_src.width:
            return 0.0
        val = dem_src.read(1, window=Window(col, row, 1, 1))[0][0]
        if val < -100: val = 0 
        norm_val = (val - DEM_MIN) / (DEM_MAX - DEM_MIN) if DEM_MAX > DEM_MIN else 0
        return max(0.0, min(1.0, norm_val))
    except Exception:
        return 0.0

def interpolate_points(p1, p2, num_steps=20):
    """插值平滑"""
    lons = np.linspace(p1[0], p2[0], num_steps)
    lats = np.linspace(p1[1], p2[1], num_steps)
    return list(zip(lons, lats))

def process_all():
    global DEM_MIN, DEM_MAX

    print(f"--- 1. 处理 DEM 数据: {PATH_DEM} ---")
    try:
        with rasterio.open(PATH_DEM) as src:
            # A. 生成高度图
            data = src.read(1)
            valid_mask = data > -1000
            if valid_mask.any():
                DEM_MIN = float(np.min(data[valid_mask]))
                DEM_MAX = float(np.max(data[valid_mask]))
            
            print(f"高程范围: {DEM_MIN}m ~ {DEM_MAX}m")
            
            # 保存高度图
            norm_data = np.zeros_like(data, dtype=np.uint8)
            if DEM_MAX > DEM_MIN:
                norm_data[valid_mask] = ((data[valid_mask] - DEM_MIN) / (DEM_MAX - DEM_MIN) * 255).astype(np.uint8)
            
            img = Image.fromarray(norm_data)
            img = img.resize((1024, int(1024 * (WORLD_HEIGHT/WORLD_WIDTH))), Image.LANCZOS)
            img.save(OUTPUT_HEIGHTMAP)
            print(f"高度图已保存: {OUTPUT_HEIGHTMAP}")

            # B. 初始化数据结构
            game_data = {
                "cities": [],
                "rivers": [],
                "timeline": [], 
                "routes": [] 
            }

            # --- C. 处理战役路线 (核心：生成时间轴和分段路线) ---
            print("--- 2. 分析战役路线 ---")
            if os.path.exists(PATH_EVENTS):
                events_gdf = gpd.read_file(PATH_EVENTS)
                events_gdf['date'] = pd.to_datetime(events_gdf['date'])
                # 必须按时间排序
                events_gdf = events_gdf.sort_values(by='date')
                # 筛选范围
                events_gdf = events_gdf.cx[BOUNDS['min_lon']:BOUNDS['max_lon'], BOUNDS['min_lat']:BOUNDS['max_lat']]
                
                # 提取节点列表
                event_nodes = []
                for _, row in events_gdf.iterrows():
                    d_str = row['date'].strftime('%Y-%m-%d')
                    event_nodes.append((row.geometry.x, row.geometry.y, d_str, row.get('name', 'Unknown')))
                
                # 1. 填充 timeline (给前端滑块显示日期用)
                game_data["timeline"] = [n[2] for n in event_nodes]

                # 2. 生成路线分段
                # 如果有N个时间点，就会有N-1段路程
                if len(event_nodes) > 1:
                    for i in range(len(event_nodes) - 1):
                        start_pt = event_nodes[i]
                        end_pt = event_nodes[i+1]
                        
                        # 向东为进攻，向西为撤退
                        is_attack = end_pt[0] >= start_pt[0]
                        
                        points_geo = interpolate_points(start_pt, end_pt, num_steps=20)
                        points_3d = []
                        for lon, lat in points_geo:
                            wx, wz = map_coords(lon, lat)
                            ny = get_height_normalized(lon, lat, src)
                            points_3d.append([wx, float(round(ny, 4)), wz])
                        
                        game_data["routes"].append({
                            "type": "attack" if is_attack else "retreat",
                            "path": points_3d,
                            "date_idx": i + 1 # 关键：这段路在到达第 i+1 个时间点时显示
                        })

                # 3. 将 Event 点也作为战役点加入
                for n in event_nodes:
                    wx, wz = map_coords(n[0], n[1])
                    ny = get_height_normalized(n[0], n[1], src)
                    game_data["cities"].append({
                        "n": n[3], "x": wx, "z": wz, "ny": float(round(ny, 4)),
                        "t": "battle"
                    })
            else:
                print("警告：未找到 events.geojson，无法生成路线！")

            # --- D. 处理河流 ---
            print("--- 3. 处理河流 ---")
            if os.path.exists(PATH_RIVERS):
                rivers_gdf = gpd.read_file(PATH_RIVERS)
                rivers_gdf = rivers_gdf.cx[BOUNDS['min_lon']:BOUNDS['max_lon'], BOUNDS['min_lat']:BOUNDS['max_lat']]
                rivers_gdf['geometry'] = rivers_gdf.simplify(0.05)
                
                for geom in rivers_gdf.geometry:
                    if geom is None: continue
                    parts = [geom] if geom.geom_type == 'LineString' else geom.geoms
                    for part in parts:
                        if part.length < 0.2: continue
                        line_pts = []
                        for x, y in part.coords:
                            wx, wz = map_coords(x, y)
                            ny = get_height_normalized(x, y, src)
                            line_pts.append([wx, float(round(ny, 4)), wz])
                        if len(line_pts) > 1:
                            game_data["rivers"].append(line_pts)

            # --- E. 处理城市 ---
            print("--- 4. 处理城市 ---")
            if os.path.exists(PATH_CITIES):
                cities_gdf = gpd.read_file(PATH_CITIES)
                cities_gdf = cities_gdf.cx[BOUNDS['min_lon']:BOUNDS['max_lon'], BOUNDS['min_lat']:BOUNDS['max_lat']]
                for _, row in cities_gdf.iterrows():
                    if row.get('POP_MAX', 0) < 50000: continue
                    wx, wz = map_coords(row.geometry.x, row.geometry.y)
                    # 简单去重
                    is_dup = False
                    for existing in game_data["cities"]:
                        if abs(existing['x'] - wx) < 2 and abs(existing['z'] - wz) < 2:
                            is_dup = True; break
                    if not is_dup:
                        ny = get_height_normalized(row.geometry.x, row.geometry.y, src)
                        game_data["cities"].append({
                            "n": row.get('NAME', 'City'),
                            "x": wx, "z": wz, "ny": float(round(ny, 4)),
                            "t": "capital" if row.get('ADM0CAP') == 1 else "city"
                        })

            # 保存
            with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, separators=(',', ':'))
            print(f"完成! 数据已保存至 {OUTPUT_JSON}")

    except Exception as e:
        print(f"处理错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_all()