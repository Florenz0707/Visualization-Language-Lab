# 开发者A个人开发计划

## 1812拿破仑东征地理可视化项目 - 数据工程师 + 后端开发

> **角色定位**: 数据工程师 + 后端开发
> **核心职责**: 历史数据处理、GIS数据工程、后端API服务
> **技术栈**: Python、pandas、GeoPandas、GDAL、rasterio、FastAPI、PostGIS
> **项目周期**: 8-10周

---

## 一、核心职责概览

### 主要工作方向

1. **历史数据挖掘与处理**
    - 1812年战役历史数据收集与验证
    - 地名标准化与地理编码
    - 数据清洗、标准化与GeoJSON转换

2. **GIS数据处理**
    - DEM（数字高程模型）数据处理
    - 等高线生成与hillshade渲染
    - 投影坐标转换（WGS84 ↔ Lambert）

3. **后端服务开发**
    - FastAPI REST API设计与实现
    - 数据查询优化与缓存策略
    - API文档与性能优化

4. **数据存储架构**
    - PostGIS数据库设计（可选）
    - GeoJSON文件组织与管理
    - 数据版本控制与provenance追踪

---

## 二、详细时间线与任务清单

### 📅 第1周：环境搭建与数据采集

#### 环境配置（Day 1-2）

- [ ] Python环境配置（Python 3.11+）
- [ ] 安装GIS核心库：

  ```bash
  pip install gdal rasterio geopandas pyproj shapely fiona
  pip install pandas numpy matplotlib
  ```

- [ ] 安装FastAPI及相关依赖：

  ```bash
  pip install fastapi uvicorn pydantic python-multipart
  pip install aiofiles httpx
  ```

- [ ] 测试GDAL命令行工具可用性

#### 数据源采集（Day 3-5）

- [ ] **历史数据收集**：
    - Charles Minard原始图表数据提取
    - 维基百科1812年战役时间线整理
    - 历史档案与学术论文数据补充
    - 收集至少50个关键事件/位置数据

- [ ] **地理数据下载**：
    - SRTM DEM数据（北纬50-60°，东经20-45°）
    - 历史地图底图（公有领域）
    - 行政区划边界数据（1812年历史边界）

#### 数据模型设计（Day 6-7）

- [ ] 设计GeoJSON Schema：
  ```json
  {
    "events": {
      "type": "FeatureCollection",
      "features": [{
        "geometry": {"type": "Point"},
        "properties": {
          "event_id": "string",
          "name": "string",
          "date": "ISO8601",
          "type": "battle|camp|city",
          "troops": "number",
          "casualties": "number",
          "faction": "french|russian|allied",
          "confidence": "0-1",
          "sources": ["string"]
        }
      }]
    }
  }
  ```

- [ ] 编写数据字典文档（`docs/data-schema.md`）
- [ ] 设计provenance元数据结构

---

### 📅 第2周：数据清洗与GeoJSON生成

#### 地名标准化（Day 1-3）

- [ ] **地理编码Pipeline**：
  ```python
  # scripts/geocoding.py
  def geocode_place(name: str, year: int = 1812) -> tuple[float, float]:
      # 1. 查询本地历史地名数据库
      # 2. 调用Nominatim API补充
      # 3. 手动校正关键地点
      pass
  ```

- [ ] 处理地名歧义（如："Smolensk" vs "Smoleńsk"）
- [ ] 构建历史地名映射表（CSV格式）

#### GeoJSON生成（Day 3-5）

- [ ] **events.geojson**：战役、城市、营地（Point）
- [ ] **movements.geojson**：军队行军轨迹（LineString）
- [ ] **territories.geojson**：控制区域、战场范围（Polygon）

- [ ] 数据验证脚本：
  ```python
  def validate_geojson(file_path: str):
      # 检查：有效几何、必需字段、时间格式、坐标范围
      pass
  ```

#### DEM处理（Day 6-7）

- [ ] **裁剪与重采样**：
  ```bash
  gdalwarp -te 20 50 45 60 -tr 0.001 0.001 \
           -t_srs EPSG:4326 input.tif output.tif
  ```

- [ ] **生成等高线**（间隔50m/100m）：
  ```bash
  gdal_contour -a elevation -i 50 dem.tif contours.shp
  ogr2ogr -f GeoJSON contours.geojson contours.shp
  ```

- [ ] **Hillshade生成**：
  ```python
  import rasterio
  from rasterio.plot import show

  def generate_hillshade(dem_path: str, output: str):
      # 使用rasterio计算hillshade
      pass
  ```

- [ ] **投影转换**（Lambert Conformal Conic）：
  ```python
  import geopandas as gpd
  gdf = gpd.read_file('events.geojson')
  gdf_lambert = gdf.to_crs('EPSG:3034')  # ETRS89-LCC
  gdf_lambert.to_file('events_lambert.geojson', driver='GeoJSON')
  ```

---

### 📅 第3周：FastAPI后端开发

#### 项目结构搭建（Day 1）

```plain_text
backend/
├── main.py              # FastAPI入口
├── api/
│   ├── __init__.py
│   ├── events.py        # 事件端点
│   ├── movements.py     # 移动端点
│   └── terrain.py       # 地形端点
├── models/
│   └── schemas.py       # Pydantic模型
├── services/
│   └── data_loader.py   # 数据加载服务
├── data/
│   ├── geojson/
│   └── rasters/
└── utils/
    └── projections.py   # 投影转换工具
```

#### 核心API端点（Day 2-5）

- [ ] **GET /api/events**
  ```python
  from fastapi import APIRouter, Query
  from datetime import date

  router = APIRouter()

  @router.get("/events")
  async def get_events(
      start: date = Query(...),
      end: date = Query(...),
      projection: str = "wgs84"
  ):
      # 1. 加载GeoJSON
      # 2. 时间过滤
      # 3. 投影转换
      # 4. 返回FeatureCollection
      pass
  ```

- [ ] **GET /api/movements**
  ```python
  @router.get("/movements")
  async def get_movements(
      unit: str | None = None,
      projection: str = "wgs84"
  ):
      # 返回指定军团的行军轨迹
      pass
  ```

- [ ] **GET /api/terrain/dem**
  ```python
  @router.get("/terrain/dem")
  async def get_dem(
      bbox: str = Query(...),  # "minx,miny,maxx,maxy"
      resolution: int = 512
  ):
      # 返回裁剪后的heightmap图片URL或Base64
      pass
  ```

- [ ] **GET /api/terrain/contours**
  ```python
  @router.get("/terrain/contours")
  async def get_contours(interval: int = 100):
      # 返回等高线GeoJSON
      pass
  ```

#### 性能优化（Day 6-7）

- [ ] **缓存策略**：
  ```python
  from functools import lru_cache

  @lru_cache(maxsize=128)
  def load_geojson(file_path: str) -> dict:
      with open(file_path) as f:
          return json.load(f)
  ```

- [ ] **CORS配置**：
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_methods=["*"]
  )
  ```

- [ ] **Gzip压缩**：
  ```python
  from fastapi.middleware.gzip import GZipMiddleware
  app.add_middleware(GZipMiddleware, minimum_size=1000)
  ```

- [ ] 测试API响应时间（目标：<100ms）

---

### 📅 第4周：统计数据与高级查询

#### 统计数据生成（Day 1-3）

- [ ] **Choropleth数据**（按月/周聚合）：
  ```python
  def aggregate_troops_by_period(
      events: gpd.GeoDataFrame,
      period: str = "month"
  ) -> gpd.GeoDataFrame:
      # 按时间段聚合兵力数据
      # 计算每个区域的兵力密度
      pass
  ```

- [ ] 添加不确定性字段（`confidence: 0-1`）
- [ ] 编写数据字典与provenance文档

#### 高级查询端点（Day 4-5）

- [ ] **GET /api/statistics/troops**
  ```python
  @router.get("/statistics/troops")
  async def get_troops_stats(
      start: date,
      end: date,
      faction: str | None = None
  ):
      # 返回时间序列兵力统计
      return {
          "french": [{"date": "...", "count": 420000}, ...],
          "russian": [...]
      }
  ```

- [ ] **GET /api/flows**
  ```python
  @router.get("/flows")
  async def get_flow_data(
      simplify: bool = True,
      threshold: float = 0.01
  ):
      # 返回flow map的起止点对
      # 应用Douglas-Peucker简化算法
      pass
  ```

#### Movement数据优化（Day 6-7）

- [ ] **路径简化**：
  ```python
  from shapely.geometry import LineString

  def simplify_path(line: LineString, tolerance: float) -> LineString:
      return line.simplify(tolerance, preserve_topology=True)
  ```

- [ ] 按军团分组（Grande Armee、各军团）
- [ ] 生成bundling预计算数据（权重、方向）

---

### 📅 第5周：Story Mode数据准备

#### 章节数据编写（Day 1-4）

- [ ] **历史叙事文本**（10-15个章节）：
    - 章节1：渡过涅曼河（1812-06-24）
    - 章节2：维尔纽斯进军（1812-06-28）
    - 章节3：斯摩棱斯克战役（1812-08-16）
    - 章节4：博罗季诺会战（1812-09-07）
    - 章节5：攻占莫斯科（1812-09-14）
    - 章节6：莫斯科大火（1812-09-15）
    - 章节7：开始撤退（1812-10-19）
    - 章节8：马洛亚罗斯拉维茨（1812-10-24）
    - 章节9：别列津纳河渡河（1812-11-26）
    - 章节10：撤出俄罗斯（1812-12-14）

- [ ] 每章包含：
    - 关键事件ID列表
    - 地理坐标与镜头参数
    - 历史背景文本（200-300字）
    - 配图来源标注

#### 配图收集（Day 5）

- [ ] 收集公有领域历史画作：
    - Napoleon crossing Niemen River
    - Battle of Borodino (Hess)
    - Moscow Fire (various artists)
    - Berezina crossing (January Suchodolski)

- [ ] 图片处理：
    - 统一尺寸（1920x1080）
    - 格式转换（WebP优化）
    - 存储至`public/images/story/`

#### 音频准备（Day 6-7，可选）

- [ ] 方案1：录制旁白音频（10-15段，每段1-2分钟）
- [ ] 方案2：使用Web Speech API（浏览器TTS）
- [ ] 方案3：AI语音生成（Azure Speech/ElevenLabs）

---

### 📅 第6周：性能优化与API完善

#### 时间窗口查询优化（Day 1-2）

- [ ] **空间索引**：
  ```python
  import rtree

  def build_spatial_index(features: list) -> rtree.index.Index:
      idx = rtree.index.Index()
      for i, feature in enumerate(features):
          bounds = shape(feature['geometry']).bounds
          idx.insert(i, bounds)
      return idx
  ```

- [ ] **时间索引**：使用B-tree或间隔树优化时间范围查询

#### LOD（Level of Detail）系统（Day 3-4）

- [ ] **多分辨率GeoJSON**：
    - High-res（zoom > 8）：完整数据
    - Mid-res（5-8）：简化路径
    - Low-res（< 5）：聚合为点

- [ ] 端点参数：
  ```python
  @router.get("/movements")
  async def get_movements(
      lod: int = Query(2, ge=1, le=3)
  ):
      # 根据LOD返回不同精度数据
      pass
  ```

#### 监控与日志（Day 5）

- [ ] 添加请求日志：
  ```python
  import logging
  from fastapi import Request

  @app.middleware("http")
  async def log_requests(request: Request, call_next):
      logger.info(f"{request.method} {request.url}")
      response = await call_next(request)
      return response
  ```

- [ ] 性能监控（Prometheus metrics，可选）

#### 数据版本控制（Day 6-7）

- [ ] Git LFS配置（管理大型GeoJSON/Raster文件）
- [ ] 数据changelog文档
- [ ] 自动化测试：
  ```python
  import pytest

  def test_events_endpoint():
      response = client.get("/api/events?start=1812-06-24&end=1812-12-14")
      assert response.status_code == 200
      assert len(response.json()['features']) > 0
  ```

---

### 📅 第7-8周：集成支持与文档完善

#### 跨团队协作（持续）

- [ ] 支持开发者C的Flow Map数据需求
- [ ] 为开发者D提供Story Mode章节数据
- [ ] 与开发者B对接API接口规范

#### 后端部署（Day 1-3）

- [ ] Docker化：
  ```dockerfile
  FROM python:3.11-slim
  RUN apt-get update && apt-get install -y gdal-bin
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . /app
  WORKDIR /app
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] 部署到云服务（Heroku/Railway/Render）
- [ ] 配置HTTPS与CDN（Cloudflare）

#### API文档（Day 4-5）

- [ ] OpenAPI/Swagger文档完善：
  ```python
  app = FastAPI(
      title="Napoleon 1812 Campaign API",
      description="Historical GIS data API for 1812 invasion visualization",
      version="1.0.0",
      docs_url="/docs",
      redoc_url="/redoc"
  )
  ```

- [ ] 编写README：
    - API端点说明
    - 数据模型说明
    - 本地开发指南
    - 部署说明

#### 数据质量保证（Day 6-7）

- [ ] 数据审查与校正（历史准确性）
- [ ] 单元测试覆盖率 > 80%
- [ ] 性能基准测试报告

---

## 三、技术栈详解

### GIS核心库

| 库名            | 用途        | 关键功能              |
|---------------|-----------|-------------------|
| **GDAL**      | 栅格/矢量数据处理 | 格式转换、投影、裁剪        |
| **rasterio**  | 栅格数据读写    | DEM处理、hillshade生成 |
| **GeoPandas** | 矢量数据操作    | GeoJSON读写、空间查询    |
| **pyproj**    | 坐标投影转换    | WGS84 ↔ Lambert   |
| **Shapely**   | 几何操作      | 简化、缓冲区、空间关系       |

### 后端框架

- **FastAPI**：异步REST API框架
- **Pydantic**：数据验证与序列化
- **Uvicorn**：ASGI服务器
- **httpx**：异步HTTP客户端（用于外部API调用）

---

## 四、关键技术挑战

### 1. 历史数据不确定性处理

**问题**：1812年历史数据存在缺失、矛盾、估算等问题。

**解决方案**：

- 为每个数据点添加`confidence`字段（0-1）
- 记录数据来源（`sources`数组）
- 提供多版本数据（乐观估计vs保守估计）

### 2. DEM数据量大

**问题**：高分辨率DEM文件可达数GB。

**解决方案**：

- 使用COG（Cloud Optimized GeoTIFF）格式
- 生成金字塔瓦片（LOD）
- 仅按需裁剪返回局部区域

### 3. 投影转换性能

**问题**：实时投影转换计算开销大。

**解决方案**：

- 预计算多种投影版本（WGS84、Lambert、Azimuthal）
- 使用缓存（Redis或内存缓存）
- 前端传递投影参数，后端返回对应文件

### 4. Flow Map数据简化

**问题**：原始轨迹点过多（>10000点）导致渲染卡顿。

**解决方案**：

- Douglas-Peucker算法简化路径
- 按zoom level提供不同精度
- 使用WebGL渲染大量几何（前端责任，后端需提供优化数据）

---

## 五、交付物清单

### 数据产物

- [ ] `events.geojson`（点要素，200-500个事件）
- [ ] `movements.geojson`（线要素，10-20条主要轨迹）
- [ ] `territories.geojson`（面要素，控制区域）
- [ ] `contours.geojson`（等高线）
- [ ] `dem_heightmap.png`（高程贴图，2048x2048）
- [ ] `hillshade.tif`（hillshade栅格）
- [ ] `chapters.json`（Story Mode章节配置）

### 代码产物

- [ ] FastAPI后端服务（可运行`uvicorn main:app`）
- [ ] 数据处理脚本（`scripts/`目录）
- [ ] 单元测试（`tests/`目录）

### 文档产物

- [ ] `docs/data-schema.md`（数据模型文档）
- [ ] `docs/api-reference.md`（API接口文档）
- [ ] `backend/README.md`（后端开发指南）
- [ ] `docs/data-provenance.md`（数据来源与处理记录）

---

## 六、里程碑检查点

### Week 2结束

- ✅ 完整GeoJSON数据集生成
- ✅ DEM处理完成
- ✅ FastAPI可访问`http://localhost:8000/docs`

### Week 4结束

- ✅ 所有核心API端点实现
- ✅ 统计数据生成
- ✅ 性能满足要求（<100ms响应）

### Week 6结束

- ✅ Story Mode数据完整
- ✅ API文档完善
- ✅ 单元测试通过

### Week 8结束

- ✅ 后端部署上线
- ✅ 数据质量审查通过
- ✅ 跨团队集成完成

---

## 七、风险管理

| 风险       | 概率 | 影响 | 缓解措施                |
|----------|----|----|---------------------|
| 历史数据缺失   | 高  | 中  | 使用估算值+低confidence标记 |
| DEM处理失败  | 中  | 高  | 准备降级方案（使用低分辨率数据）    |
| API性能不达标 | 中  | 中  | 提前进行性能测试，优化查询逻辑     |
| 投影转换错误   | 低  | 高  | 使用标准EPSG代码，充分测试     |

---

## 八、学习资源

### 推荐教程

- **GDAL官方文档**：https://gdal.org/
- **GeoPandas用户指南**：https://geopandas.org/
- **FastAPI教程**：https://fastapi.tiangolo.com/
- **PostGIS入门**：https://postgis.net/workshops/

### 参考论文

- Minard, C. J. (1869). *Napoleon's 1812 Russian Campaign*
- Kraak, M. J. (2003). *The space-time cube revisited from a geovisualization perspective*

---

## 九、协作接口

### 与开发者B的接口

- **输出**：GeoJSON数据、API端点URL
- **输入**：前端需求（字段格式、投影类型）
- **会议频率**：每周2次（周一需求对齐、周五集成测试）

### 与开发者C的接口

- **输出**：DEM heightmap、简化后的flow数据
- **输入**：纹理分辨率要求、数据精度需求

### 与开发者D的接口

- **输出**：Story章节数据、统计数据API
- **输入**：章节时间点、需要高亮的事件ID

---

## 十、每日工作流程建议

### 上午（9:00-12:00）

1. 查看团队日报，同步其他成员进度
2. 处理紧急数据需求（如其他开发者提出的查询需求）
3. 核心开发任务（数据处理/API开发）

### 下午（13:30-17:30）

1. 代码审查与测试
2. 文档编写
3. 跨团队协作会议（如有安排）
4. 学习与技术调研

### 晚上（可选）

- 阅读历史资料，补充领域知识
- 技术博客学习（GIS、数据可视化）

---

## 总结

作为数据工程师与后端开发，你的工作是整个项目的**数据基础**。高质量的数据处理和稳定的API服务将直接影响前端可视化效果。

**核心目标**：

1. **数据准确性**：历史数据经过充分验证，provenance清晰
2. **API性能**：响应时间<100ms，支持并发请求
3. **代码质量**：单元测试覆盖率>80%，文档完善
4. **团队协作**：及时响应其他开发者的数据需求

**成功标准**：

- 所有API端点正常工作，前端能顺利集成
- 数据质量经过历史学家审查通过
- 性能测试满足并发100用户需求
- 文档完善，其他开发者能独立使用API

加油！🚀
