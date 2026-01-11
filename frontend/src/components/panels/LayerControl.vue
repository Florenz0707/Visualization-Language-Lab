<template>
  <div class="layer-control">
    <div class="panel-header">
      <h3 class="title">🗺️ 图层控制</h3>
    </div>

    <div class="layer-list">
      <label v-for="layer in layers" :key="layer.id" class="layer-item">
        <input
          type="checkbox"
          :checked="isLayerVisible(layer.id)"
          @change="toggleLayer(layer.id)"
          class="layer-checkbox"
        />
        <span class="layer-icon">{{ layer.icon }}</span>
        <span class="layer-name">{{ layer.name }}</span>
      </label>
    </div>

    <div class="projection-control">
      <h4 class="subtitle">🌐 投影方式</h4>
      <select v-model="currentProjection" @change="onProjectionChange" class="projection-select">
        <option value="wgs84">WGS84 (标准)</option>
        <option value="webmercator">Web Mercator</option>
        <option value="lambert">Lambert (兰伯特)</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMapStore } from '@/stores/map'

const mapStore = useMapStore()

const layers = ref([
  { id: 'events', name: '事件点', icon: '📍' },
  { id: 'movements', name: '行军轨迹', icon: '➡️' },
  { id: 'territories', name: '控制区域', icon: '🗺️' }
])

const currentProjection = computed({
  get: () => mapStore.projection,
  set: (value) => mapStore.setProjection(value)
})

const isLayerVisible = (layerId) => {
  return mapStore.visibleLayers.includes(layerId)
}

const toggleLayer = (layerId) => {
  mapStore.toggleLayer(layerId)
}

const onProjectionChange = () => {
  console.log('Projection changed to:', currentProjection.value)
}
</script>

<style scoped>
.layer-control {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  backdrop-filter: blur(10px);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.panel-header {
  margin-bottom: 16px;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.subtitle {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 6px;
}

.layer-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px 12px;
  border-radius: 10px;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.6);
}

.layer-item:hover {
  background: rgba(59, 130, 246, 0.08);
  transform: translateX(2px);
}

.layer-checkbox {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
}

.layer-icon {
  font-size: 16px;
}

.layer-name {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
  flex: 1;
}

.projection-control {
  padding-top: 16px;
  border-top: 2px solid rgba(226, 232, 240, 0.6);
}

.projection-select {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  transition: all 0.2s ease;
}

.projection-select:hover {
  border-color: #3b82f6;
}

.projection-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
