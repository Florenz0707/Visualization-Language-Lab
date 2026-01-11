import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useMapStore = defineStore('map', () => {
  // State
  const currentTime = ref(new Date('1812-06-24'))
  const timeRange = ref({
    start: new Date('1812-06-24'),
    end: new Date('1812-12-14')
  })
  const playbackSpeed = ref(1)
  const isPlaying = ref(false)
  const visibleLayers = ref(['events', 'movements', 'territories', 'flows'])
  const projection = ref('wgs84')
  const selectedUnits = ref([])
  const mapInstance = ref(null)

  // Computed
  const currentTimeString = computed(() => {
    return currentTime.value.toISOString().split('T')[0]
  })

  const timeRangeString = computed(() => {
    return {
      start: timeRange.value.start.toISOString().split('T')[0],
      end: timeRange.value.end.toISOString().split('T')[0]
    }
  })

  // Actions
  const setCurrentTime = (date) => {
    currentTime.value = date instanceof Date ? date : new Date(date)
  }

  const setTimeRange = (start, end) => {
    timeRange.value = {
      start: start instanceof Date ? start : new Date(start),
      end: end instanceof Date ? end : new Date(end)
    }
  }

  const setPlaybackSpeed = (speed) => {
    playbackSpeed.value = speed
  }

  const togglePlayback = () => {
    isPlaying.value = !isPlaying.value
  }

  const setPlaying = (playing) => {
    isPlaying.value = playing
  }

  const toggleLayer = (layerName) => {
    const index = visibleLayers.value.indexOf(layerName)
    if (index > -1) {
      visibleLayers.value.splice(index, 1)
    } else {
      visibleLayers.value.push(layerName)
    }
  }

  const setVisibleLayers = (layers) => {
    visibleLayers.value = layers
  }

  const setProjection = (proj) => {
    projection.value = proj
  }

  const setMapInstance = (map) => {
    mapInstance.value = map
  }

  const selectUnit = (unitId) => {
    if (!selectedUnits.value.includes(unitId)) {
      selectedUnits.value.push(unitId)
    }
  }

  const deselectUnit = (unitId) => {
    const index = selectedUnits.value.indexOf(unitId)
    if (index > -1) {
      selectedUnits.value.splice(index, 1)
    }
  }

  const clearSelectedUnits = () => {
    selectedUnits.value = []
  }

  return {
    // State
    currentTime,
    timeRange,
    playbackSpeed,
    isPlaying,
    visibleLayers,
    projection,
    selectedUnits,
    mapInstance,
    // Computed
    currentTimeString,
    timeRangeString,
    // Actions
    setCurrentTime,
    setTimeRange,
    setPlaybackSpeed,
    togglePlayback,
    setPlaying,
    toggleLayer,
    setVisibleLayers,
    setProjection,
    setMapInstance,
    selectUnit,
    deselectUnit,
    clearSelectedUnits
  }
})
