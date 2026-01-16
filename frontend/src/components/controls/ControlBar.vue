<template>
  <div class="control-bar">
    <!-- 时间轴控制 -->
    <div class="time-controls">
      <button @click="togglePlayback" class="control-btn">
        {{ mapStore.isPlaying ? '⏸' : '▶' }}
      </button>
      <button @click="resetTime" class="control-btn">⏹</button>

      <input
        type="range"
        :min="minTime"
        :max="maxTime"
        :value="currentTimeValue"
        @input="onTimeChange"
        class="time-slider"
      />

      <span class="time-label">{{ formattedDate }}</span>

      <select v-model="mapStore.playbackSpeed" class="speed-select">
        <option :value="1">1x</option>
        <option :value="2">2x</option>
        <option :value="5">5x</option>
      </select>
    </div>

    <!-- 图层控制 -->
    <div class="layer-controls">
      <label v-for="layer in layers" :key="layer.id" class="layer-checkbox">
        <input
          type="checkbox"
          :checked="isLayerVisible(layer.id)"
          @change="toggleLayer(layer.id)"
        />
        <span>{{ layer.name }}</span>
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useMapStore } from '@/stores/map'

const mapStore = useMapStore()
const playbackInterval = ref(null)

const layers = ref([
  { id: 'events', name: '事件' },
  { id: 'movements', name: '行军' },
  { id: 'territories', name: '区域' },
  { id: 'flows', name: '流向' }
])

const minTime = computed(() => mapStore.timeRange.start.getTime())
const maxTime = computed(() => mapStore.timeRange.end.getTime())
const currentTimeValue = computed(() => mapStore.currentTime.getTime())

const formattedDate = computed(() => {
  return mapStore.currentTime.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

const onTimeChange = (event) => {
  const timestamp = parseInt(event.target.value)
  mapStore.setCurrentTime(new Date(timestamp))
}

const togglePlayback = () => {
  mapStore.togglePlayback()
}

const resetTime = () => {
  mapStore.setPlaying(false)
  mapStore.setCurrentTime(mapStore.timeRange.start)
}

const isLayerVisible = (layerId) => {
  return mapStore.visibleLayers.includes(layerId)
}

const toggleLayer = (layerId) => {
  mapStore.toggleLayer(layerId)
}

watch(() => mapStore.isPlaying, (isPlaying) => {
  if (isPlaying) {
    startPlayback()
  } else {
    stopPlayback()
  }
})

const startPlayback = () => {
  if (playbackInterval.value) return
  const dayInMs = 24 * 60 * 60 * 1000
  playbackInterval.value = setInterval(() => {
    const newTime = new Date(mapStore.currentTime.getTime() + dayInMs * mapStore.playbackSpeed)
    if (newTime > mapStore.timeRange.end) {
      mapStore.setCurrentTime(mapStore.timeRange.start)
    } else {
      mapStore.setCurrentTime(newTime)
    }
  }, 100)
}

const stopPlayback = () => {
  if (playbackInterval.value) {
    clearInterval(playbackInterval.value)
    playbackInterval.value = null
  }
}

onUnmounted(() => {
  stopPlayback()
})
</script>

<style scoped>
.control-bar {
  display: flex;
  align-items: center;
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.time-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.control-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.time-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.2);
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.time-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
}

.time-label {
  color: white;
  font-size: 14px;
  font-weight: 500;
  min-width: 120px;
}

.speed-select,
.projection-select {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.layer-controls {
  display: flex;
  gap: 16px;
}

.layer-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.projection-control {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-size: 14px;
}
</style>
