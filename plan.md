# 1812拿破仑东征地理可视化项目执行计划

> **项目周期**: 8-10周（2个月）
> **团队规模**: 4人全职开发
> **交付日期**: 2025年3月初
> **项目难度**: ⭐⭐⭐⭐⭐

---

## 一、团队分工与角色定义

### 👨‍💻 开发者A：数据工程师 + 后端开发

**核心职责**：

- 历史数据挖掘、清洗与标准化
- GIS数据处理（DEM、等高线、投影转换）
- FastAPI后端服务开发
- PostGIS/数据存储架构设计

**技能要求**：Python、pandas、GeoPandas、GDAL、rasterio、FastAPI、SQL

---

### 👨‍💻 开发者B：前端架构师 + 地图可视化

**核心职责**：

- Vue 3项目架构搭建（Pinia、Router）
- Mapbox GL JS集成与地图引擎配置
- 基础图层实现（Choropleth、Symbol、Isolines）
- 投影切换与多图层管理

**技能要求**：Vue 3、TypeScript、Mapbox GL JS、GeoJSON、CSS3

---

### 👨‍💻 开发者C：3D可视化专家 + 高级动画

**核心职责**：

- Three.js 3D地形渲染
- DEM heightmap集成与shader开发
- Seam-carving风格2D→3D动画
- Flow Map + Edge-bundling算法实现

**技能要求**：Three.js、WebGL、GLSL、计算几何、d3-force

---

### 👨‍💻 开发者D：交互设计师 + Story Mode开发

**核心职责**：

- UI/UX设计与组件开发
- 时间轴控制器与回放系统
- Story Mode章节系统与镜头动画
- 统计面板与Arc Diagrams（d3.js）

**技能要求**：Vue 3、D3.js、动画设计、交互设计、Playwright

---

## 二、详细时间线（8-10周）

### 📅 第1-2周：环境搭建 + 数据准备 + 架构设计

#### Week 1: 项目初始化与数据采集

**全员任务**：

- [ ] 项目kickoff会议，明确需求与技术栈
- [ ] Git仓库规范、分支策略、代码审查流程
- [ ] 环境配置统一（Node.js 20+、pnpm、Python 3.11+）

**开发者A（数据+后端）**：

- [ ] 收集1812年战役历史数据源（Charles Minard图表、维基百科、历史档案）
- [ ] 设计数据模型（GeoJSON schema、时间字段格式、provenance元数据）
- [ ] 下载SRTM DEM数据（东欧-俄罗斯：北纬50-60°，东经20-45°）
- [ ] 环境搭建：安装GDAL、rasterio、geopandas、pyproj

**开发者B（前端架构）**：

- [ ] 清理Vue模板代码，安装依赖：

  ```bash
  pnpm add mapbox-gl @types/mapbox-gl pinia vue-router axios @vueuse/core
  pnpm add -D @types/geojson
  ```

- [ ] 注册Mapbox账号，获取Access Token
- [ ] 搭建项目目录结构：

  ```plain_text
  src/
    ├── stores/          # Pinia状态管理
    ├── services/        # API服务层
    ├── components/
    │   ├── map/         # 地图相关组件
    │   ├── timeline/    # 时间轴组件
    │   ├── panels/      # 侧栏面板
    │   └── story/       # Story Mode
    ├── utils/           # 工具函数
    └── types/           # TypeScript类型定义
  ```

**开发者C（3D可视化）**：

- [ ] 安装Three.js与相关库：

  ```bash
  pnpm add three @types/three @react-three/fiber lil-gui
  ```

- [ ] 研究DEM数据格式与heightmap纹理生成方案
- [ ] 搭建Three.js测试场景（基础地形plane + camera控制）

**开发者D（交互+Story）**：

- [ ] 设计UI/UX原型（Figma/Sketch）：
  - 主地图布局（全屏）
  - 时间轴位置（底部）
  - 侧栏统计面板（右侧可折叠）
  - Story Mode控制器（浮动窗口）
- [ ] 安装D3.js相关工具：

  ```bash
  pnpm add d3 @types/d3 d3-force d3-shape
  ```

**交付物**：

- ✅ 数据模型设计文档（`docs/data-schema.md`）
- ✅ 技术架构图（`docs/architecture.md`）
- ✅ UI设计稿与交互原型
- ✅ 初步的1812战役数据CSV（至少50个事件/位置）

---

#### Week 2: 数据处理Pipeline + 核心架构搭建

**开发者A（数据+后端）**：

- [ ] **数据清洗与GeoJSON生成**：
  - 地名标准化（"Moscow" → `{lat: 55.7558, lon: 37.6173}`）
  - 构建`events.geojson`（点要素：战役、城市、营地）
  - 构建`movements.geojson`（线要素：军队行军轨迹）
  - 构建`territories.geojson`（面要素：控制区域、战场范围）
- [ ] **DEM处理**：
  - GDAL裁剪SRTM为项目区域
  - 生成等高线GeoJSON（间隔50m/100m）
  - 生成hillshade栅格瓦片（png格式）
  - pyproj投影转换（WGS84 → Lambert Conformal Conic）
- [ ] **FastAPI项目初始化**：

  ```python
  backend/
    ├── main.py
    ├── api/
    │   ├── events.py
    │   ├── movements.py
    │   └── terrain.py
    ├── data/
    │   ├── geojson/
    │   └── rasters/
    └── utils/
        └── projections.py
  ```

- [ ] 实现API端点：
  - `GET /api/events?start=1812-06-24&end=1812-12-14`
  - `GET /api/movements?unit=Grande_Armee&projection=lambert`
  - `GET /api/terrain/dem` （返回heightmap图片URL）

**开发者B（前端架构）**：

- [ ] **Pinia状态管理设计**：

  ```typescript
  // stores/map.ts
  export const useMapStore = defineStore('map', {
    state: () => ({
      currentTime: new Date('1812-06-24'),
      playbackSpeed: 1,
      visibleLayers: ['events', 'movements', 'terrain'],
      projection: 'lambert', // 'wgs84' | 'lambert' | 'azimuthal'
      selectedUnits: []
    })
  })
  ```

- [ ] **MapContainer组件**：
  - Mapbox GL JS初始化（center: Moscow, zoom: 5）
  - 响应式容器（100vw x 100vh - UI元素高度）
  - 基础控制器（zoom、rotation、pitch）
- [ ] **API Service层**：

  ```typescript
  // services/api.ts
  export const fetchEvents = (timeRange: TimeRange) => {...}
  export const fetchMovements = (filters: MovementFilters) => {...}
  ```

**开发者C（3D可视化）**：

- [ ] **Three.js地形Mesh创建**：
  - 从DEM数据生成PlaneGeometry（512x512顶点）
  - Vertex shader读取heightmap纹理修改顶点高度
  - 基础材质（Phong材质 + 纹理贴图）
- [ ] **与Mapbox集成方案**：
  - 研究Mapbox Custom Layer API
  - 实现`TerrainLayer.vue`组件（将Three.js场景注入Mapbox）

**开发者D（交互+Story）**：

- [ ] **基础UI组件库**：
  - `Button.vue`、`Slider.vue`、`Panel.vue`
  - 统一设计系统（颜色、字体、间距）
- [ ] **TimelineSlider组件**：
  - D3.js绘制时间轴（1812年6月-12月）
  - 滑块拖拽交互 → 更新Pinia `currentTime`
  - 播放/暂停按钮、速度控制（1x/2x/5x）

**交付物**：

- ✅ 完整GeoJSON数据集（events.geojson, movements.geojson, territories.geojson）
- ✅ DEM处理产物（heightmap.png, contours.geojson, hillshade瓦片）
- ✅ FastAPI后端可运行（`http://localhost:8000/docs`）
- ✅ Mapbox地图可正常加载与交互

---

### 📅 第3-4周：核心可视化图层实现

#### Week 3: Choropleth + Symbol Maps + 时间联动

**开发者A（数据+后端）**：

- [ ] **统计数据生成**：
  - 按月/周聚合兵力数据（choropleth分级方案）
  - 计算不确定性字段（confidence: 0-1）
  - 添加数据字典与provenance文档
- [ ] **后端性能优化**：
  - 实现数据缓存（Redis或内存缓存）
  - GeoJSON压缩传输（gzip）
  - 分页与LOD（Level of Detail）端点

**开发者B（前端架构）**：

- [ ] **Choropleth Map实现**：

  ```javascript
  // components/map/ChoroplethLayer.vue
  map.addLayer({
    id: 'choropleth',
    type: 'fill',
    source: 'territories',
    paint: {
      'fill-color': [
        'interpolate', ['linear'], ['get', 'troops'],
        0, '#f7fbff',
        50000, '#6baed6',
        100000, '#08519c'
      ],
      'fill-opacity': 0.7
    }
  })
  ```

- [ ] **Symbol/Dot Map实现**：
  - 圆圈大小 → 兵力（radius: sqrt(troops) * scale）
  - 颜色 → 阵营（French: blue, Russian: red, Allied: green）
  - 透明度 → 置信度（opacity: confidence）
- [ ] **图层管理器**：
  - `LayerControl.vue`：复选框开关各图层
  - 监听Pinia `visibleLayers`变化 → `map.setLayoutProperty`

**开发者C（3D可视化）**：

- [ ] **3D地形优化**：
  - 添加光照系统（DirectionalLight + AmbientLight）
  - 实现动态LOD（近处高精度，远处简化）
  - 性能监控（FPS、drawcalls）
- [ ] **Isolines/Surface实现**：
  - 加载等高线GeoJSON → Mapbox line layer
  - Hillshade栅格叠加（raster-dem-source）
  - 图层开关切换2D等高线/3D地形

**开发者D（交互+Story）**：

- [ ] **时间轴与地图联动**：
  - 监听`currentTime`变化 → 过滤GeoJSON要素（`['<=', ['get', 'timestamp'], currentTime]`）
  - 实现回放功能：setInterval每100ms更新时间
  - 添加时间标签显示（"1812年7月15日"）
- [ ] **StatisticsPanel组件**：
  - D3.js柱状图：法军vs俄军兵力对比
  - D3.js折线图：累计损失变化
  - 实时更新（响应时间变化）

**交付物**：

- ✅ Choropleth与Symbol图层可视化完成
- ✅ 时间轴回放功能正常运行
- ✅ 侧栏统计面板实时联动
- ✅ 3D地形基础渲染完成

---

#### Week 4: Flow Map + Edge Bundling（高难度）

**开发者A（数据+后端）**：

- [ ] **Movement数据优化**：
  - 构建起止点对（source → target + weight）
  - 路径简化（Douglas-Peucker算法，减少冗余点）
  - 按军团分组（Grande Armee、各军团）
- [ ] 提供bundling预计算服务（可选）

**开发者C（3D可视化）** — **本周主力任务**：

- [ ] **Flow Map基础实现**：
  - Mapbox LineLayer绘制原始轨迹
  - 线宽 → 兵力（width: log(troops)）
  - 颜色 → 方向（前进：蓝色，撤退：红色）
- [ ] **Edge Bundling算法**：
  - 方案1（推荐）：使用`d3-force`模拟力导向bundling
  - 方案2：实现hierarchical edge bundling（基于控制点层次聚类）
  - 生成平滑B-spline曲线（d3.curveCatmullRom）
- [ ] **WebGL高性能渲染**：
  - 使用Mapbox Custom Layer + Three.js LineGeometry
  - 或deck.gl PathLayer（可选技术栈）
  - 实现渐变效果（起点→终点颜色过渡）
- [ ] **交互优化**：
  - Hover高亮单条流线
  - 点击显示详情（军团名称、兵力、日期范围）

**开发者B（前端架构）**：

- [ ] 协助C实现Mapbox与Three.js的深度集成
- [ ] **投影切换功能**：
  - UI按钮：WGS84 / Lambert / Azimuthal
  - 切换时重新请求后端对应投影的GeoJSON
  - 平滑过渡动画

**开发者D（交互+Story）**：

- [ ] **Arc Diagram实现**：
  - 独立SVG画布（`<svg>` in `ArcDiagram.vue`）
  - D3.js绘制事件序列圆弧图（时间轴弧形连接）
  - Brush交互 → 修改主地图时间范围

**交付物**：

- ✅ Flow Map基础版本（直线轨迹）
- ✅ Edge Bundling算法原型（可能需要调优）
- ✅ 投影切换功能完成
- ✅ Arc Diagram事件序列视图

**⚠️ 风险提示**：Edge Bundling是本项目最复杂模块，如Week 4结束时未达到理想效果，准备降级方案（简单贝塞尔曲线 + 透明度叠加模拟bundling效果）。

---

### 📅 第5-6周：3D动画 + Story Mode核心

#### Week 5: Seam-Carving风格2D→3D动画

**开发者C（3D可视化）** — **本周主力任务**：

- [ ] **动画系统设计**：
  - 使用GSAP或Three.js Tween库
  - 定义动画阶段（5秒总时长）：
    1. 0-1s: Camera拉近平面地图
    2. 1-3s: 地形逐步"浮出"（顶点高度 0 → DEM值）
    3. 3-4s: 光照增强，阴影出现
    4. 4-5s: Camera倾斜至45°俯视角
- [ ] **Vertex Shader实现**：

  ```glsl
  uniform float uProgress; // 0 → 1
  uniform sampler2D uHeightmap;

  void main() {
    vec4 heightData = texture2D(uHeightmap, uv);
    float height = heightData.r * 5000.0; // 高程缩放
    vec3 pos = position;
    pos.z += height * uProgress; // 逐步抬升
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
  ```

- [ ] **纹理处理（可选）**：
  - Python预处理：scikit-image seam-carving对地图纹理做content-aware缩放
  - 生成10帧transition纹理序列
  - Shader逐帧切换纹理（模拟seam reveal效果）
- [ ] **触发机制**：
  - 按钮："切换到3D视图"
  - Story Mode章节自动触发

**开发者D（交互+Story）** — **Story Mode开发开始**：

- [ ] **章节配置系统**：

  ```json
  // public/story/chapters.json
  [
    {
      "id": 1,
      "title": "渡过涅曼河：战役开始",
      "timestamp": "1812-06-24",
      "duration": 8000,
      "camera": {
        "center": [24.0, 54.9],
        "zoom": 7,
        "pitch": 0,
        "bearing": 0
      },
      "layers": ["events", "movements"],
      "highlights": ["event_001"],
      "annotation": {
        "text": "1812年6月24日，拿破仑率领61万大军渡过涅曼河，入侵俄罗斯...",
        "image": "/images/neman_crossing.jpg",
        "audio": "/audio/chapter1.mp3"
      }
    },
    // ... 10-15个章节
  ]
  ```

- [ ] **StoryController组件**：
  - 读取chapters.json
  - 状态机：idle → playing → paused → completed
  - 进度条显示当前章节
  - 上一步/下一步按钮

**开发者B（前端架构）**：

- [ ] **Camera动画封装**：

  ```typescript
  // utils/cameraAnimation.ts
  export const flyToChapter = (map: mapboxgl.Map, chapter: Chapter) => {
    map.flyTo({
      center: chapter.camera.center,
      zoom: chapter.camera.zoom,
      pitch: chapter.camera.pitch,
      bearing: chapter.camera.bearing,
      duration: 2000,
      essential: true
    })
  }
  ```

- [ ] 协助D实现图层高亮功能
- [ ] 性能优化：代码分割、懒加载

**开发者A（数据+后端）**：

- [ ] **Story章节数据准备**：
  - 编写10-15个章节的历史叙事文本
  - 收集配图（公有领域历史画作）
  - 确定每章关键事件与地理位置
- [ ] 录制旁白音频（可选，或使用Web Speech API）

**交付物**：

- ✅ 2D→3D动画完成（至少基础浮出效果）
- ✅ Story Mode章节配置完成
- ✅ StoryController基础功能实现
- ✅ Camera自动飞行动画

---

#### Week 6: Story Mode完善 + 全功能集成

**开发者D（交互+Story）**：

- [ ] **AnnotationOverlay组件**：
  - 半透明黑色遮罩 + 中心白色文本框
  - Markdown渲染章节文本
  - 图片展示（响应式布局）
  - 音频播放器（HTML5 Audio API）
- [ ] **自动播放逻辑**：

  ```typescript
  const autoPlay = async () => {
    for (const chapter of chapters) {
      await playChapter(chapter)
      await sleep(chapter.duration)
    }
  }
  ```

- [ ] **手动控制增强**：
  - 键盘快捷键（←/→ 切换章节，Space 暂停）
  - 触摸手势支持（移动端）

**开发者A（数据+后端）**：

- [ ] **时间窗口查询优化**：
  - 添加索引（时间戳字段）
  - 实现"回放包"导出API：`GET /api/export?start=...&end=...` 返回完整GeoJSON压缩包
- [ ] 文档编写：API使用手册、数据字典

**开发者B（前端架构）**：

- [ ] **响应式布局优化**：
  - 桌面端（≥1920px）：侧栏固定，地图居中
  - 平板端（768-1919px）：侧栏可折叠
  - 移动端（<768px）：全屏地图，UI浮动覆盖
- [ ] **暗色模式支持**（可选）

**开发者C（3D可视化）**：

- [ ] **3D性能优化**：
  - 实现WebGL2 instancing（大量符号渲染）
  - Frustum culling（视锥剔除）
  - 纹理压缩（KTX2格式）
- [ ] Edge Bundling最终调优

**全员任务**：

- [ ] **集成测试**：
  - 测试所有图层组合开启/关闭
  - 测试投影切换 + 时间回放联动
  - 测试Story Mode完整流程
  - 跨浏览器测试（Chrome、Firefox、Safari、Edge）

**交付物**：

- ✅ Story Mode完整功能（文本+图片+音频+动画）
- ✅ 所有可视化图层集成完成
- ✅ 响应式布局适配
- ✅ 核心功能通过集成测试

---

### 📅 第7-8周：测试、文档、演示视频

#### Week 7: E2E测试 + Bug修复

**开发者D（交互+Story）** + **开发者B（前端架构）**：

- [ ] **Playwright E2E测试套件**：

  ```typescript
  // tests/e2e/story-mode.spec.ts
  test('Story Mode完整播放', async ({ page }) => {
    await page.goto('/')
    await page.click('[data-testid="story-mode-btn"]')
    await page.waitForSelector('.annotation-overlay')
    // 验证章节内容、地图位置、图层状态
  })
  ```

- [ ] 关键测试场景：
  - 地图加载与交互（缩放、平移、旋转）
  - 时间轴拖拽与回放
  - 图层切换与联动
  - Story Mode自动播放
  - 投影切换
  - 3D动画触发
- [ ] **性能测试**：
  - Lighthouse评分（目标：Performance > 80）
  - 内存泄漏检测
  - 大数据量加载测试（>10000个点）

**开发者A（数据+后端）**：

- [ ] **后端单元测试**：
  - pytest覆盖所有API端点
  - 投影转换函数测试
  - 数据查询性能测试
- [ ] **数据验证**：
  - GeoJSON格式校验（geojsonlint）
  - 历史数据准确性审查

**开发者C（3D可视化）**：

- [ ] 修复3D渲染bug
- [ ] 性能profile与优化

**全员任务**：

- [ ] Bug修复冲刺
- [ ] 代码审查（Code Review）
- [ ] 性能优化

---

#### Week 8: 文档 + 演示视频 + 部署

**开发者A（数据+后端）**：

- [ ] **数据文档**：
  - `docs/data-provenance.md`：数据来源、引用、授权
  - `docs/data-dictionary.md`：字段说明、单位、格式
- [ ] **API文档**：
  - 补充FastAPI Swagger注释
  - 编写API使用示例

**开发者B（前端架构）**：

- [ ] **技术文档**：
  - `docs/architecture.md`：系统架构图、技术栈说明
  - `docs/deployment.md`：部署指南（Vercel/Netlify/GitHub Pages）
  - `README.md`：项目介绍、安装步骤、使用方法
- [ ] **CI/CD配置**：
  - GitHub Actions自动构建与测试
  - 自动部署到预览环境

**开发者D（交互+Story）** — **演示视频制作**：

- [ ] **录屏准备**：
  - 准备演示脚本（5-8分钟完整流程）
  - 清理开发工具与控制台
  - 设置最佳视觉效果（高分辨率、流畅帧率）
- [ ] **录制与剪辑**：
  - 使用OBS Studio录屏（1920x1080, 60fps）
  - 分段录制：
    1. 项目介绍（30s）
    2. 数据加载与地图浏览（1min）
    3. 时间轴回放演示（1.5min）
    4. 各图层切换展示（1.5min）
    5. 3D动画演示（1min）
    6. Story Mode完整播放（2-3min）
    7. 总结与技术亮点（30s）
  - 使用DaVinci Resolve/Premiere Pro剪辑
  - 添加字幕、背景音乐、转场效果
- [ ] 导出发布（YouTube/Bilibili）

**开发者C（3D可视化）**：

- [ ] 最终视觉调优
- [ ] 协助录制技术演示

**全员任务**：

- [ ] **最终验收**：
  - 功能清单逐项检查
  - 用户验收测试（UAT）
  - 性能指标达标确认
- [ ] **发布准备**：
  - 版本号标记（v1.0.0）
  - Release Notes编写
  - 许可证文件（MIT/Apache 2.0）

---

### 📅 第9-10周：缓冲与高级功能（可选）

> 如果前8周进度顺利，可用于实现高级功能或应对延期风险

**可选高级功能**：

- [ ] **多语言支持**（中文/英文切换）
- [ ] **数据导出功能**（截图、GeoJSON下载、PDF报告）
- [ ] **高级滤镜**（按军团、阵营、事件类型筛选）
- [ ] **VR/AR模式**（WebXR实验性支持）
- [ ] **社交分享**（生成分享卡片、嵌入代码）

---

## 三、技术栈详细说明

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 数据处理与API服务 |
| **FastAPI** | 0.109+ | RESTful API框架 |
| **pandas** | 2.2+ | 表格数据处理 |
| **GeoPandas** | 0.14+ | 地理数据处理 |
| **rasterio** | 1.3+ | 栅格数据读写 |
| **GDAL** | 3.8+ | GIS数据转换 |
| **pyproj** | 3.6+ | 投影转换 |
| **scikit-image** | 0.22+ | 图像处理（seam-carving） |
| **Pillow** | 10.2+ | 纹理生成 |
| **uvicorn** | 0.27+ | ASGI服务器 |

**安装命令**：

```bash
pip install fastapi uvicorn pandas geopandas rasterio pyproj scikit-image pillow python-multipart
```

---

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.5+ | 前端框架 |
| **Vite** | 7.2+ | 构建工具 |
| **TypeScript** | 5.6+ | 类型安全 |
| **Pinia** | 2.2+ | 状态管理 |
| **Vue Router** | 4.4+ | 路由管理 |
| **Mapbox GL JS** | 3.7+ | 地图渲染引擎 |
| **Three.js** | 0.170+ | 3D渲染 |
| **D3.js** | 7.9+ | 数据可视化 |
| **Axios** | 1.7+ | HTTP客户端 |
| **@vueuse/core** | 11.2+ | Vue组合式工具 |
| **GSAP** | 3.12+ | 动画库 |
| **Turf.js** | 7.1+ | 空间分析 |

**安装命令**：

```bash
pnpm add mapbox-gl three d3 pinia vue-router axios @vueuse/core gsap @turf/turf
pnpm add -D @types/mapbox-gl @types/three @types/d3 @types/geojson typescript
```

**开发依赖**：

```bash
pnpm add -D playwright @playwright/test vitest @vue/test-utils jsdom
```

---

## 四、风险管理与备选方案

### 高风险项与应对策略

#### 🔴 风险1：Edge Bundling算法实现复杂度高

**影响**：可能延期1-2周或效果不理想

**备选方案**：

- **Plan A**：使用现成库`d3-force`简化实现
- **Plan B**：降级为"分组线条 + 透明度叠加"模拟bundling视觉效果
- **Plan C**：完全移除bundling，仅保留基础flow map

**决策点**：Week 4结束时评估，如进度落后>3天立即启动Plan B

---

#### 🔴 风险2：Seam-Carving动画研发难度大

**影响**：技术实现可能失败或消耗过多时间

**备选方案**：

- **Plan A（推荐）**：使用"顶点高度渐变动画"（类seam-carving风格但技术简单）
- **Plan B**：传统3D地形翻转动画（类似Google Earth）
- **Plan C**：去掉动画，仅提供2D/3D视图切换按钮

**决策点**：Week 5中期（第3天）评估Three.js原型，如无法达到60fps或视觉效果差立即切换Plan A

---

#### 🟡 风险3：历史数据不足或不准确

**影响**：可视化缺乏真实性

**应对措施**：

- 使用Charles Minard经典图表作为"金标准"数据源
- 不确定数据标注confidence字段（0.3-1.0）
- 在UI显示"数据仅供教学演示，非历史精确复原"免责声明
- 提供数据provenance文档说明来源与局限性

---

#### 🟡 风险4：Mapbox投影切换技术限制

**影响**：可能无法实现多投影无缝切换

**备选方案**：

- 后端预投影 → 前端GeoJSON绘制（放弃Mapbox原生投影）
- 仅提供WGS84 + Lambert两种投影（去掉Azimuthal）
- 使用Leaflet + Proj4.js替代Mapbox（技术栈调整）

**决策点**：Week 2结束时技术验证

---

#### 🟢 风险5：浏览器性能限制（低端设备）

**影响**：移动端或老旧电脑无法流畅运行

**应对措施**：

- 实现自适应LOD（检测FPS自动降低渲染精度）
- 提供"低性能模式"开关（关闭3D、减少粒子数）
- 目标设备：近3年桌面浏览器 + 中高端移动设备

---

## 五、质量保证检查清单

### 功能完整性（必须100%完成）

- [ ] **地图基础功能**
  - [ ] 地图加载与交互（缩放、平移、旋转、倾斜）
  - [ ] 三种投影切换（WGS84、Lambert、Azimuthal）
  - [ ] 响应式布局（桌面/平板/移动）

- [ ] **可视化图层**
  - [ ] Choropleth Map（等值区域图）
  - [ ] Symbol/Dot Map（符号点图）
  - [ ] Flow Map（行军流线）
  - [ ] Edge Bundling（流线束化，可降级）
  - [ ] Arc Diagram（事件序列视图）
  - [ ] Isolines/Surface（等高线与hillshade）
  - [ ] 3D地形渲染
  - [ ] 2D→3D动画（可降级）

- [ ] **时间控制系统**
  - [ ] 时间轴滑块（拖拽改变时间）
  - [ ] 播放/暂停/重置按钮
  - [ ] 速度调节（1x/2x/5x）
  - [ ] 时间范围选择（brush交互）
  - [ ] 所有图层响应时间变化

- [ ] **Story Mode**
  - [ ] 章节配置加载
  - [ ] 自动播放功能
  - [ ] 手动导航（上一步/下一步）
  - [ ] Camera自动飞行动画
  - [ ] 注释显示（文字+图片）
  - [ ] 图层高亮与联动
  - [ ] 键盘快捷键

- [ ] **侧栏统计面板**
  - [ ] 兵力对比图表（D3.js）
  - [ ] 损失统计曲线
  - [ ] 实时数据更新

- [ ] **后端API**
  - [ ] 事件查询端点
  - [ ] 移动轨迹查询
  - [ ] 地形数据服务
  - [ ] 时间窗口过滤
  - [ ] 投影转换服务
  - [ ] 回放包导出

---

### 性能指标

- [ ] **前端性能**
  - [ ] Lighthouse Performance Score ≥ 80
  - [ ] First Contentful Paint < 1.5s
  - [ ] Largest Contentful Paint < 2.5s
  - [ ] 地图帧率 ≥ 30fps（桌面）、≥ 20fps（移动）
  - [ ] 3D渲染帧率 ≥ 60fps（无bundling时）

- [ ] **后端性能**
  - [ ] API响应时间 < 200ms（简单查询）
  - [ ] GeoJSON压缩传输（gzip减少60%+体积）
  - [ ] 支持并发请求 ≥ 50 req/s

---

### 浏览器兼容性

- [ ] Chrome 120+ ✅
- [ ] Firefox 121+ ✅
- [ ] Safari 17+ ✅
- [ ] Edge 120+ ✅
- [ ] 移动端Safari iOS 16+ ✅
- [ ] 移动端Chrome Android 12+ ✅

---

### 测试覆盖

- [ ] **单元测试**
  - [ ] 前端组件测试覆盖率 ≥ 60%
  - [ ] 后端API测试覆盖率 ≥ 80%

- [ ] **E2E测试**
  - [ ] 关键用户流程测试（≥10个场景）
  - [ ] 跨浏览器自动化测试

- [ ] **手动测试**
  - [ ] 完整功能演示流程无bug
  - [ ] 极端数据测试（空数据、超大数据）
  - [ ] 网络异常处理（离线、慢速）

---

## 六、交付物清单

### 代码交付

- [ ] **前端代码**
  - [ ] Vue 3项目完整源码
  - [ ] TypeScript类型定义
  - [ ] 单元测试与E2E测试
  - [ ] Vite配置与构建脚本
  - [ ] `.env.example`环境变量模板

- [ ] **后端代码**
  - [ ] FastAPI完整源码
  - [ ] pytest测试套件
  - [ ] requirements.txt依赖清单
  - [ ] Docker配置（可选）

- [ ] **数据文件**
  - [ ] GeoJSON数据集（events, movements, territories）
  - [ ] DEM heightmap与hillshade瓦片
  - [ ] Story Mode章节配置JSON
  - [ ] 历史配图与音频文件

---

### 文档交付

- [ ] **README.md**
  - [ ] 项目介绍与功能列表
  - [ ] 技术栈说明
  - [ ] 安装与运行步骤
  - [ ] 环境变量配置
  - [ ] 常见问题（FAQ）

- [ ] **技术文档**
  - [ ] `docs/architecture.md`：系统架构设计
  - [ ] `docs/api-reference.md`：API接口文档
  - [ ] `docs/data-schema.md`：数据模型说明
  - [ ] `docs/data-provenance.md`：数据来源与溯源
  - [ ] `docs/deployment.md`：部署指南
  - [ ] `docs/development.md`：开发指南

- [ ] **用户手册**
  - [ ] `docs/user-guide.md`：使用说明
  - [ ] 操作截图与说明

---

### 演示交付

- [ ] **演示视频**
  - [ ] 5-8分钟完整功能演示
  - [ ] 1920x1080分辨率，60fps
  - [ ] 中英文字幕
  - [ ] 发布到YouTube/Bilibili

- [ ] **在线Demo**
  - [ ] 部署到公开URL（Vercel/Netlify）
  - [ ] 稳定运行，无明显bug
  - [ ] 提供访问链接与二维码

---

## 七、团队协作规范

### Git工作流

```plain_text
main (受保护，仅通过PR合并)
├── develop (开发主分支)
│   ├── feature/map-container (开发者B)
│   ├── feature/3d-terrain (开发者C)
│   ├── feature/story-mode (开发者D)
│   └── feature/data-pipeline (开发者A)
└── release/v1.0.0 (发布分支)
```

**分支命名规范**：

- `feature/<功能名>`: 新功能开发
- `bugfix/<问题描述>`: Bug修复
- `hotfix/<紧急修复>`: 紧急修复
- `refactor/<重构模块>`: 代码重构

**提交信息规范**：

```plain_text
feat: 添加Choropleth图层渲染
fix: 修复时间轴拖拽卡顿问题
docs: 更新API文档
perf: 优化3D渲染性能
test: 添加Story Mode E2E测试
```

---

### 代码审查流程

1. 功能开发完成后提交PR到`develop`
2. 至少1名其他开发者审查（建议跨领域审查）
3. 通过自动化测试（CI）
4. 合并后删除feature分支

---

### 每日站会（15分钟）

- **时间**: 每天上午10:00
- **内容**:
  1. 昨天完成了什么？
  2. 今天计划做什么？
  3. 遇到什么阻碍？

---

### 周会（1小时）

- **时间**: 每周一上午11:00
- **内容**:
  1. 上周进度回顾
  2. 本周任务分配
  3. 风险识别与应对
  4. 技术难题讨论

---

## 八、成功标准

### 最低可交付版本（MVP）

- ✅ 基础地图加载与交互
- ✅ 至少3种可视化图层（Choropleth + Symbol + Isolines）
- ✅ 时间轴回放功能
- ✅ Story Mode基础功能（5个章节）
- ✅ 后端API正常运行
- ✅ 演示视频完成

### 完整版本

- ✅ MVP所有功能
- ✅ Flow Map + Edge Bundling
- ✅ 3D地形与2D→3D动画
- ✅ Arc Diagram事件序列视图
- ✅ 投影切换功能
- ✅ 10+章节完整Story Mode
- ✅ E2E测试通过
- ✅ 完整技术文档

### 优秀标准

- ✅ 完整版本所有功能
- ✅ Seam-Carving风格动画成功实现
- ✅ 性能优化（Lighthouse > 90）
- ✅ 支持移动端完整功能
- ✅ 多语言支持
- ✅ 数据导出功能
- ✅ 社区反馈积极（GitHub stars > 50）

---

## 九、预算与资源

### 开发成本估算（仅参考）

| 项目 | 成本 | 说明 |
|------|------|------|
| **Mapbox API** | $0 | 免费额度50k加载/月（足够开发+演示） |
| **服务器** | $0-20 | Vercel免费部署前端，后端可用Railway免费tier |
| **域名** | $10-15/年 | 可选，用于正式部署 |
| **历史资料** | $0 | 使用公有领域资源 |
| **开发工具** | $0 | 全部使用开源软件 |
| **总计** | **$10-35** | 极低成本项目 |

---

### 开发环境要求

**硬件**：

- CPU: i5-10代及以上（推荐i7或M1/M2 Mac）
- 内存: 16GB+（推荐32GB）
- 显卡: 支持WebGL 2.0（集成显卡可，独显更佳）
- 硬盘: 50GB+可用空间（SSD）

**软件**：

- Node.js 20+
- pnpm 8+
- Python 3.11+
- Git 2.40+
- VS Code（推荐插件：Vue - Official, Prettier, ESLint）

---

## 十、联系与支持

### 项目管理

- **项目经理**: [指定1人负责进度跟踪]
- **技术负责人**: [指定1人负责架构决策]

### 沟通渠道

- **日常沟通**: Slack/Discord/微信群
- **代码托管**: GitHub/GitLab
- **文档协作**: Notion/Confluence
- **设计协作**: Figma

### 问题上报

- 阻塞性问题：立即在群内@全员
- 技术难题：创建GitHub Issue讨论
- 需求变更：周会提出并投票决策

---

## 十一、附录

### 推荐学习资源

**Mapbox GL JS**:

- 官方文档: https://docs.mapbox.com/mapbox-gl-js/
- 示例库: https://docs.mapbox.com/mapbox-gl-js/example/

**Three.js**:

- 官方文档: https://threejs.org/docs/
- Three.js Journey课程: https://threejs-journey.com/

**D3.js**:

- Observable教程: https://observablehq.com/@d3/learn-d3
- D3 Graph Gallery: https://d3-graph-gallery.com/

**Edge Bundling**:

- 论文: Holten & Van Wijk (2009) "Force-Directed Edge Bundling"
- 实现参考: https://github.com/upphiminn/d3.ForceBundle

**GIS数据处理**:

- GeoPandas文档: https://geopandas.org/
- GDAL教程: https://gdal.org/tutorials/

---

### 历史参考资料

- Charles Joseph Minard's 1812 Map (经典可视化案例)
- Wikipedia: French invasion of Russia
- 《战争与和平》（托尔斯泰）— 小说但包含历史细节
- David Chandler's "The Campaigns of Napoleon" (学术著作)

---

**文档版本**: v1.0
**最后更新**: 2025年12月29日
**负责人**: [项目负责人姓名]

---

🎯 **项目口号**: "用现代技术重现历史的时空演化，让数据讲述战争的故事！"
