<template>
  <div class="map-demo">
    <div class="demo-header">
      <h1>地图数据API测试</h1>
      <div class="controls">
        <select v-model="selectedMapType" @change="loadMapData">
          <option value="countries">国家边界</option>
          <option value="provinces">省份</option>
          <option value="cities_major">主要城市</option>
          <option value="rivers">河流</option>
        </select>

        <label>
          <input type="checkbox" v-model="useSimplify" @change="loadMapData" />
          简化几何
        </label>

        <button @click="loadMapData" :disabled="loading">
          {{ loading ? '加载中...' : '重新加载' }}
        </button>
      </div>
    </div>

    <div class="demo-content">
      <!-- 统计信息 -->
      <div class="stats-panel">
        <div class="stat-item">
          <span class="label">数据类型:</span>
          <span class="value">{{ selectedMapType }}</span>
        </div>
        <div class="stat-item">
          <span class="label">Features数量:</span>
          <span class="value">{{ featureCount }}</span>
        </div>
        <div class="stat-item">
          <span class="label">加载时间:</span>
          <span class="value">{{ loadTime }}ms</span>
        </div>
        <div class="stat-item">
          <span class="label">数据大小:</span>
          <span class="value">{{ dataSize }}</span>
        </div>
      </div>

      <!-- 地图显示区域 -->
      <div ref="mapContainer" class="map-display"></div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import axios from 'axios'

const mapContainer = ref(null)
const map = ref(null)
const selectedMapType = ref('cities_major')
const useSimplify = ref(false)
const loading = ref(false)
const error = ref(null)
const mapData = ref(null)
const loadTime = ref(0)
const currentLayer = ref(null)

// 计算属性
const featureCount = computed(() => {
  return mapData.value?.features?.length || 0
})

const dataSize = computed(() => {
  if (!mapData.value) return '0 KB'
  const size = JSON.stringify(mapData.value).length
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  return `${(size / 1024 / 1024).toFixed(2)} MB`
})

// 初始化地图
const initMap = () => {
  if (!mapContainer.value) return

  map.value = L.map(mapContainer.value).setView([55.0, 30.0], 4)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value)
}

// 加载地图数据
const loadMapData = async () => {
  loading.value = true
  error.value = null
  const startTime = Date.now()

  try {
    const params = {
      simplify: useSimplify.value,
      tolerance: 0.01
    }

    const response = await axios.get(`http://localhost:9000/api/maps/${selectedMapType.value}`, { params })

    mapData.value = response.data
    loadTime.value = Date.now() - startTime

    // 渲染到地图
    renderMapData()
  } catch (err) {
    error.value = `加载失败: ${err.message}`
    console.error('Error loading map data:', err)
  } finally {
    loading.value = false
  }
}

// 渲染地图数据
const renderMapData = () => {
  if (!map.value || !mapData.value) return

  // 移除旧图层
  if (currentLayer.value) {
    map.value.removeLayer(currentLayer.value)
  }

  // 添加新图层
  currentLayer.value = L.geoJSON(mapData.value, {
    style: {
      color: '#3b82f6',
      weight: 2,
      opacity: 0.6
    },
    pointToLayer: (feature, latlng) => {
      return L.circleMarker(latlng, {
        radius: 5,
        fillColor: '#ef4444',
        color: '#fff',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
      })
    }
  }).addTo(map.value)

  // 自动缩放到数据范围
  if (mapData.value.features.length > 0) {
    map.value.fitBounds(currentLayer.value.getBounds())
  }
}

// 生命周期
onMounted(() => {
  initMap()
  loadMapData()
})
</script>

<style scoped>
.map-demo {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.demo-header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.demo-header h1 {
  margin: 0 0 16px 0;
  font-size: 24px;
  color: #1e293b;
}

.controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.controls select,
.controls button {
  padding: 8px 16px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
}

.controls button {
  background: #3b82f6;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.controls button:hover:not(:disabled) {
  background: #2563eb;
}

.controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.demo-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item .label {
  font-size: 12px;
  color: #64748b;
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.map-display {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.error-message {
  padding: 16px;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 8px;
  border: 1px solid #fca5a5;
}
</style>
