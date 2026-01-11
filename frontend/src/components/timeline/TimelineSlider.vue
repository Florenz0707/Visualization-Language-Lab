<template>
  <div class="timeline-container">
    <div class="timeline-controls">
      <button @click="togglePlayback" class="control-btn play-btn" :title="mapStore.isPlaying ? '暂停' : '播放'">
        <span v-if="mapStore.isPlaying">⏸</span>
        <span v-else>▶</span>
      </button>
      <button @click="resetTime" class="control-btn reset-btn" title="重置">
        ⏹
      </button>
      <select v-model="mapStore.playbackSpeed" class="speed-select">
        <option :value="1">1x</option>
        <option :value="2">2x</option>
        <option :value="5">5x</option>
      </select>
      <div class="time-label">{{ formattedDate }}</div>
    </div>

    <div class="timeline-slider">
      <input
        type="range"
        :min="minTime"
        :max="maxTime"
        :value="currentTimeValue"
        @input="onTimeChange"
        class="slider"
      />
      <div class="timeline-marks">
        <span class="mark-label">1812年6月</span>
        <span class="mark-label">1812年12月</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useMapStore } from '@/stores/map'

const mapStore = useMapStore()
const playbackInterval = ref(null)

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
  const intervalMs = 100

  playbackInterval.value = setInterval(() => {
    const newTime = new Date(mapStore.currentTime.getTime() + dayInMs * mapStore.playbackSpeed)

    if (newTime > mapStore.timeRange.end) {
      mapStore.setCurrentTime(mapStore.timeRange.start)
    } else {
      mapStore.setCurrentTime(newTime)
    }
  }, intervalMs)
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
.timeline-container {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  backdrop-filter: blur(10px);
  padding: 20px 30px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  min-width: 500px;
  max-width: 700px;
  z-index: 1000;
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.timeline-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.control-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
}

.control-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.control-btn:active {
  transform: translateY(0);
}

.reset-btn {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  box-shadow: 0 4px 12px rgba(100, 116, 139, 0.3);
}

.reset-btn:hover {
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  box-shadow: 0 6px 16px rgba(100, 116, 139, 0.4);
}

.speed-select {
  padding: 8px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  transition: all 0.2s ease;
}

.speed-select:hover {
  border-color: #3b82f6;
}

.speed-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.time-label {
  margin-left: auto;
  font-size: 15px;
  color: #1e293b;
  font-weight: 600;
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.08);
  border-radius: 8px;
}

.timeline-slider {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right, #e2e8f0 0%, #cbd5e1 100%);
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
  transition: all 0.2s ease;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
  transition: all 0.2s ease;
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
}

.timeline-marks {
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
}

.mark-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

@media (max-width: 768px) {
  .timeline-container {
    min-width: calc(100vw - 40px);
    padding: 16px 20px;
    bottom: 20px;
  }

  .time-label {
    font-size: 13px;
    padding: 6px 12px;
  }
}
</style>
