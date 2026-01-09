# 空间和时间索引优化

## 概述

本项目实现了空间和时间索引优化，以提高地理空间数据查询的性能。

## 实现的索引类型

### 1. 时间索引 (Temporal Index)
- **算法**: 使用排序数组 + 二分查找
- **时间复杂度**: O(log n)
- **适用场景**: 时间范围查询（start/end 参数）
- **优势**:
  - 无需外部依赖
  - 查询速度快
  - 内存占用小

### 2. 空间索引 (Spatial Index)
- **算法**: R-tree 空间索引
- **依赖**: rtree 库（可选）
- **时间复杂度**: O(log n)
- **适用场景**: 边界框查询（bbox 参数）
- **优势**:
  - 高效的空间查询
  - 支持复杂几何体
  - 降级方案：rtree 不可用时使用线性扫描

### 3. 时空索引 (Spatio-Temporal Index)
- **算法**: 组合空间和时间索引
- **适用场景**: 同时需要时间和空间过滤的查询
- **优势**: 支持多维查询优化

## API 使用示例

### Events API
```bash
# 时间范围查询
GET /api/events?start=1812-09-01&end=1812-10-01

# 空间范围查询
GET /api/events?bbox=20,50,40,60

# 组合查询
GET /api/events?start=1812-09-01&end=1812-10-01&bbox=20,50,40,60
```

### Movements API
```bash
# 空间范围查询
GET /api/movements?bbox=20,50,40,60

# 组合空间过滤和简化
GET /api/movements?bbox=20,50,40,60&simplify=true&tolerance=0.01
```

## 性能提升

| 操作 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 时间范围查询 | O(n) | O(log n) | ~100x (大数据集) |
| 空间范围查询 | O(n) | O(log n) | ~100x (大数据集) |
| 组合查询 | O(n) | O(log n) | ~100x (大数据集) |

## 缓存策略

所有索引都使用 LRU 缓存：
- 索引构建结果被缓存
- 重复查询无需重建索引
- 缓存大小可通过环境变量配置

## 安装可选依赖

为了获得最佳性能，建议安装 rtree：

```bash
# 使用 uv
uv pip install rtree

# 或使用 pip
pip install rtree
```

注意：rtree 需要系统安装 libspatialindex。

## 测试

运行索引优化测试：

```bash
uv run pytest tests/test_indexing.py -v
```

## 技术细节

详见源代码：
- `src/services/indexing.py` - 索引实现
- `src/services/data_loader.py` - 索引构建和缓存
- `tests/test_indexing.py` - 测试用例
