# LOD (Level of Detail) 系统

## 概述

LOD系统为地图可视化提供多分辨率数据支持，根据缩放级别自动选择合适的数据精度，优化性能和用户体验。

## LOD 级别定义

| LOD | 描述 | 适用Zoom | 容差 | 数据类型 |
|-----|------|----------|------|----------|
| 1 | 最高细节 | > 8 | 0.00005 | LineString |
| 2 | 高细节 | 7-8 | 0.0001 | LineString |
| 3 | 中等细节 | 6-7 | 0.0005 | LineString |
| 4 | 中低细节 | 5-6 | 0.001 | LineString |
| 5 | 低细节 | 4-5 | 0.005 | LineString |
| 6 | 很低细节 | 3-4 | 0.01 | LineString |
| 7 | 最低细节 | < 3 | - | Point (聚合) |

## Zoom 到 LOD 映射

```python
ZOOM_TO_LOD = {
    0: 7, 1: 7, 2: 7,           # 很远 - 聚合点
    3: 6, 4: 6,                 # 远 - 高度简化
    5: 5, 6: 4,                 # 中距离 - 简化
    7: 3, 8: 2,                 # 近 - 详细
    9: 1, 10: 1, 11: 1, 12: 1,  # 很近 - 完整细节
}
```

## API 使用

### 方式1: 使用 zoom 参数（推荐）

前端根据地图缩放级别自动选择LOD：

```bash
GET /api/movements?zoom=8
```

### 方式2: 直接指定 LOD

手动指定LOD级别：

```bash
GET /api/movements?lod=3
```

### 方式3: 组合使用

如果同时提供 `lod` 和 `zoom`，`lod` 优先：

```bash
GET /api/movements?zoom=8&lod=5
# 使用 LOD 5，忽略 zoom 参数
```

## 预计算 LOD 文件

### 生成预计算文件

运行预计算脚本生成所有LOD级别的文件：

```bash
uv run python scripts/precompute_movements_lods.py
```

生成的文件：
- `data/geojson/movements_lod_1.geojson` - 最高细节
- `data/geojson/movements_lod_2.geojson` - 高细节
- `data/geojson/movements_lod_3.geojson` - 中等细节
- `data/geojson/movements_lod_4.geojson` - 中低细节
- `data/geojson/movements_lod_5.geojson` - 低细节
- `data/geojson/movements_lod_6.geojson` - 很低细节
- `data/geojson/movements_lod_7.geojson` - 聚合点

### 降级策略

如果预计算文件不存在，API会自动降级：
1. 尝试加载 `movements_lod_{lod}.geojson`
2. 如果文件不存在，使用对应的容差值即时简化
3. 对于LOD 7，如果聚合文件不存在，使用高容差简化

## 实现细节

### 路径简化

使用 Douglas-Peucker 算法简化LineString几何：

```python
def simplify_geojson(gj: Dict[str, Any], tolerance: float) -> Dict[str, Any]:
    """简化GeoJSON中的LineString几何"""
    # 使用shapely的simplify方法
    # preserve_topology=True 保持拓扑正确性
```

### 点聚合

对于最低LOD级别，将移动路径聚合为点：

```python
def aggregate_to_points(gj: Dict[str, Any], group_by: str = "unit"):
    """将LineString聚合为Point"""
    # 按unit分组
    # 计算每组的质心
    # 累计统计信息（count, total_events）
```


## 性能优势

### 数据量对比

以1812年战役数据为例：

| LOD | 数据类型 | 文件大小 | 特征数量 | 性能提升 |
|-----|----------|----------|----------|----------|
| 原始 | LineString | ~5MB | 1000+ | 基准 |
| LOD 1 | LineString | ~4.5MB | 1000+ | 10% |
| LOD 3 | LineString | ~2MB | 1000+ | 60% |
| LOD 5 | LineString | ~500KB | 1000+ | 90% |
| LOD 7 | Point | ~50KB | 50-100 | 99% |

### 网络传输优化

- **低缩放级别**: 使用LOD 7，传输量减少99%
- **中等缩放**: 使用LOD 3-5，传输量减少60-90%
- **高缩放级别**: 使用LOD 1-2，保持细节


## 前端集成建议

### D3.js 示例

```javascript
// 监听地图缩放事件
map.on('zoom', function() {
  const zoom = Math.floor(map.getZoom());

  // 根据zoom级别请求数据
  fetch(`/api/movements?zoom=${zoom}&bbox=${getBBox()}`)
    .then(res => res.json())
    .then(data => updateVisualization(data));
});
```

### 缓存策略

建议前端实现LOD级别的缓存：
- 缓存每个LOD级别的数据
- 缩放时优先使用缓存
- 仅在bbox变化时重新请求

## 测试

运行LOD功能测试：

```bash
uv run pytest tests/test_lod.py -v
```

## 相关文件

- `src/services/movement_utils.py` - LOD实现
- `src/api/movements.py` - API端点
- `scripts/precompute_movements_lods.py` - 预计算脚本
- `tests/test_lod.py` - 测试用例
