# 1812拿破仑东征可视化前端

基于 Vue 3 + Mapbox GL JS + D3.js 的历史地理可视化项目前端。

## 功能特性

- 📍 **交互式地图**: 基于 Mapbox GL JS 的地图展示
- ⏱️ **时间轴控制**: 可拖拽的时间轴，支持播放/暂停/速度调节
- 📊 **统计面板**: D3.js 绘制的兵力统计图表
- 🗺️ **多图层支持**: 事件点、行军轨迹、控制区域
- 📖 **故事模式**: 章节式历史叙事，带音频和图片
- 🎯 **投影切换**: 支持 WGS84、Web Mercator、Lambert 投影

## 技术栈

- Vue 3.5+
- Vite 7.2+
- Pinia (状态管理)
- Mapbox GL JS 3.17+
- D3.js 7.9+
- Axios (HTTP 客户端)

## 快速开始

### 1. 安装依赖

```bash
cd frontend
pnpm install
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:9000
VITE_MAPBOX_TOKEN=your_mapbox_token_here
```

**获取 Mapbox Token**:
1. 访问 https://account.mapbox.com/
2. 注册/登录账号
3. 在 Access Tokens 页面创建新 token
4. 复制 token 到 `.env` 文件

### 3. 启动开发服务器

```bash
pnpm dev
```

前端将运行在 http://localhost:9010

### 4. 确保后端运行

前端需要后端 API 支持，确保后端服务运行在 `http://localhost:9000`：

```bash
cd ../backend
uv run uvicorn src.main:app --reload --port 9000
```

## 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── map/              # 地图相关组件
│   │   │   └── MapContainer.vue
│   │   ├── timeline/         # 时间轴组件
│   │   │   └── TimelineSlider.vue
│   │   ├── panels/           # 侧边栏面板
│   │   │   ├── LayerControl.vue
│   │   │   └── StatisticsPanel.vue
│   │   └── story/            # 故事模式
│   │       └── StoryMode.vue
│   ├── stores/               # Pinia 状态管理
│   │   ├── map.js
│   │   └── story.js
│   ├── services/             # API 服务层
│   │   └── api.js
│   ├── types/                # 类型定义
│   │   └── index.js
│   ├── App.vue               # 主应用组件
│   └── main.js               # 应用入口
├── .env                      # 环境变量配置
├── vite.config.js            # Vite 配置
└── package.json
```

## 使用说明

### 基础操作

1. **地图导航**
   - 鼠标拖拽：平移地图
   - 滚轮：缩放
   - 右键拖拽：旋转地图

2. **时间轴控制**
   - 拖动滑块：改变当前时间
   - 播放按钮：自动播放时间线
   - 速度选择：1x/2x/5x 播放速度

3. **图层控制**
   - 勾选/取消：显示/隐藏图层
   - 投影切换：改变地图投影方式

4. **故事模式**
   - 点击"📖 故事模式"按钮进入
   - 自动播放章节内容
   - 支持上一章/下一章导航

### API 端点

前端通过以下 API 获取数据：

- `GET /api/events` - 事件数据
- `GET /api/movements` - 行军轨迹
- `GET /api/territories` - 控制区域
- `GET /api/statistics/troops` - 兵力统计
- `GET /api/story/outline` - 故事大纲
- `GET /api/story/tts/{chapter_id}` - 章节音频

## 开发指南

### 添加新图层

1. 在 `MapContainer.vue` 的 `loadLayers()` 方法中添加新的数据源和图层
2. 在 `LayerControl.vue` 中添加图层控制选项
3. 在 `map.js` store 中更新 `visibleLayers` 默认值

### 自定义样式

主要样式文件：
- `App.vue` - 全局样式
- 各组件的 `<style scoped>` - 组件样式

### 状态管理

使用 Pinia stores：
- `useMapStore()` - 地图状态（时间、图层、投影等）
- `useStoryStore()` - 故事模式状态

## 构建生产版本

```bash
pnpm build
```

构建产物在 `dist/` 目录。

## 预览生产版本

```bash
pnpm preview
```

## 故障排除

### Mapbox 地图不显示

- 检查 `.env` 中的 `VITE_MAPBOX_TOKEN` 是否正确
- 打开浏览器控制台查看错误信息
- 确认 Mapbox token 有效且未过期

### API 请求失败

- 确认后端服务运行在 `http://localhost:9000`
- 检查浏览器控制台的网络请求
- 验证后端 API 是否正常响应

### 时间轴不工作

- 检查后端是否返回了正确的时间范围数据
- 查看浏览器控制台是否有 JavaScript 错误

## 浏览器兼容性

- Chrome 120+
- Firefox 121+
- Safari 17+
- Edge 120+

## 许可证

MIT
