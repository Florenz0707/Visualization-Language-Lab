<template>
  <div class="dashboard">
    <!-- 全屏地图 -->
    <div class="map-container">
      <MapContainer />
    </div>

    <!-- 左侧温度面板 -->
    <div class="left-panel">
      <div class="temperature-panel-wrapper">
        <Temperature />
      </div>
    </div>

    <!-- 右侧悬浮面板 -->
    <div class="right-panels">
      <!-- 兵力统计面板 -->
      <div class="panel-wrapper">
        <StatisticsPanel />
      </div>

      <!-- 事件序列面板 -->
      <div class="panel-wrapper">
        <ArcDiagram />
      </div>
    </div>

    <!-- 底部控制栏 -->
    <div class="bottom-controls">
      <ControlBar />
    </div>
  </div>
</template>

<script setup>
import MapContainer from './map/MapContainer.vue'
import ControlBar from './controls/ControlBar.vue'
import StatisticsPanel from './panels/StatisticsPanel.vue'
import ArcDiagram from './panels/ArcDiagram.vue'
import Temperature from './panels/Temperature.vue'
</script>

<style scoped>
.dashboard {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
}

/* 左侧温度面板样式 - 放大且独立放置 */
.left-panel {
  position: fixed;
  top: 20px;
  left: 20px;
  width: 500px; /* 宽度放大，比右侧面板更宽 */
  max-height: calc(100vh - 80px); /* 高度占满大部分视口 */
  z-index: 50;
}

.temperature-panel-wrapper {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  overflow-y: auto;
  height: 100%; /* 高度铺满父容器 */
  display: flex;
  flex-direction: column;
}

.temperature-panel-wrapper::-webkit-scrollbar {
  width: 8px; /* 滚动条加宽，适配放大的面板 */
}

.temperature-panel-wrapper::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

/* 右侧面板样式（保持原有） */
.right-panels {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 400px;
  max-height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 50;
}

.panel-wrapper {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  overflow-y: auto;
  max-height: 45vh;
  display: flex;
  flex-direction: column;
}

.panel-wrapper::-webkit-scrollbar {
  width: 6px;
}

.panel-wrapper::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.bottom-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, transparent 100%);
  padding: 20px;
  pointer-events: none;
}

.bottom-controls > * {
  pointer-events: auto;
}
</style>