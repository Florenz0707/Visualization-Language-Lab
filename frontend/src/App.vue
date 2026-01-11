<template>
  <div id="app">
    <StoryMode />

    <div class="main-container">
      <MapContainer />

      <div class="side-panel">
        <LayerControl />
        <StatisticsPanel />
      </div>

      <TimelineSlider />
    </div>
  </div>
</template>

<script setup>
import MapContainer from './components/map/MapContainer.vue'
import TimelineSlider from './components/timeline/TimelineSlider.vue'
import LayerControl from './components/panels/LayerControl.vue'
import StatisticsPanel from './components/panels/StatisticsPanel.vue'
import StoryMode from './components/story/StoryMode.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow: hidden;
}

#app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #f8fafc;
}

.main-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
}

.side-panel {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 1000;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
  padding-right: 4px;
}

/* 自定义滚动条 */
.side-panel::-webkit-scrollbar {
  width: 6px;
}

.side-panel::-webkit-scrollbar-track {
  background: transparent;
}

.side-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.side-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* PC 端优化 */
@media (min-width: 1024px) {
  .side-panel {
    width: 380px;
  }
}

@media (min-width: 1440px) {
  .side-panel {
    width: 420px;
    top: 30px;
    right: 30px;
  }
}

/* 平板适配 */
@media (max-width: 1023px) {
  .side-panel {
    width: 320px;
    top: 15px;
    right: 15px;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .side-panel {
    width: calc(100vw - 30px);
    max-width: 400px;
    top: 10px;
    right: 10px;
  }
}
</style>
