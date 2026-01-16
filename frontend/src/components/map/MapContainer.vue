<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useMapStore } from '@/stores/map'
import { fetchEvents, fetchTerritories, fetchFlows } from '@/services/api' // 注意：这里暂时去掉了 fetchMovements，因为我们改为动态生成轨迹

const mapContainer = ref(null)
const map = ref(null)
const mapStore = useMapStore()

// 动态图层组
const layerGroups = ref({
  events: null,     // 用于显示点（圆点）
  trajectory: null, // 用于显示动态生成的连线
  territories: null,
  flows: null
})

// 静态背景图层组
const mapLayerGroups = ref({
  countries: null,
  provinces: null,
  cities_major: null,
  rivers: null
})

// 存储所有原始数据
const allData = ref({
  eventsList: [], // 扁平化并排序后的事件数组
  territories: null,
  flows: null
})

onMounted(async () => {
  initMap()
  initLayerGroups()
  await loadData()
  await loadStaticMapLayers()
  
  // 初始化完成后，根据当前时间渲染一次
  if (mapStore.currentTime) {
    updateMapByTime(mapStore.currentTime)
  }
})

// 1. 初始化地图实例
const initMap = () => {
  map.value = L.map(mapContainer.value, {
    center: [55.0, 30.0],
    zoom: 4.5,
    zoomControl: true,
    minZoom: 3,
    maxZoom: 10
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value)

  mapStore.setMapInstance(map.value)
}

// 2. 初始化空图层组（关键：先添加到地图，后续只操作数据增删）
const initLayerGroups = () => {
  // 轨迹线在下，点在上，所以先添加轨迹层
  layerGroups.value.trajectory = L.layerGroup().addTo(map.value)
  layerGroups.value.events = L.layerGroup().addTo(map.value)
  
  layerGroups.value.territories = L.layerGroup().addTo(map.value)
  layerGroups.value.flows = L.layerGroup().addTo(map.value)
}

// 3. 加载核心数据
const loadData = async () => {
  try {
    // --- 加载 Events 并排序 ---
    const eventsData = await fetchEvents({ projection: mapStore.projection })
    
    if (eventsData && eventsData.features) {
      // 关键：按时间戳升序排序，确保连线顺序正确
      allData.value.eventsList = eventsData.features.sort((a, b) => {
        return new Date(a.properties.date).getTime() - new Date(b.properties.date).getTime()
      })
    }
  } catch (error) {
    console.error('Error loading events:', error)
  }

  // 加载领土等其他数据...
  try {
    const territoriesData = await fetchTerritories({ projection: mapStore.projection })
    // 这里简单处理，直接显示领土，或者也可以根据时间过滤（如果领土有变动）
    // 此处示例为直接显示
    L.geoJSON(territoriesData, {
        style: (feature) => ({
            fillColor: feature.properties.faction === 'french' ? '#3b82f6' : '#ef4444',
            weight: 1, opacity: 0.5, fillOpacity: 0.2
        })
    }).addTo(layerGroups.value.territories)
  } catch (e) { console.error(e) }
}

// 4. 加载静态背景图层 (省份、河流等)
const loadStaticMapLayers = async () => {
  const mapLayerTypes = ['countries', 'provinces', 'cities_major', 'rivers']
  
  for (const layerId of mapLayerTypes) {
    try {
      // 假设这是你的本地API地址
      const response = await fetch(`http://localhost:9000/api/maps/${layerId}?simplify=true`)
      const data = await response.json()

      const layer = L.geoJSON(data, {
        style: (feature) => {
          if (layerId === 'rivers') return { color: '#3b82f6', weight: 1.5, opacity: 0.5 }
          return { fillColor: 'transparent', color: '#94a3b8', weight: 1, opacity: 0.6 }
        },
        pointToLayer: (feature, latlng) => {
          if (layerId === 'cities_major') {
            return L.circleMarker(latlng, { radius: 3, color: '#f59e0b', weight: 1 })
          }
        }
      })
      
      mapLayerGroups.value[layerId] = layer
      // 默认是否显示取决于 mapStore 的初始设置，这里暂不自动添加，由 toggle 控制
    } catch (error) {
      console.error(`Error loading ${layerId}:`, error)
    }
  }
  
  // 注册 Toggle 回调
  mapStore.setMapLayerToggleFunction(toggleMapLayerVisibility)
}

// 核心逻辑：监听时间变化
watch(() => mapStore.currentTime, (newTime) => {
  updateMapByTime(newTime)
})

const updateMapByTime = (currentTime) => {
  if (!map.value || !allData.value.eventsList.length) return

  const currentTimestamp = new Date(currentTime).getTime()

  // 1. 筛选出当前时间点之前发生的所有事件
  const visibleEvents = allData.value.eventsList.filter(feature => {
    const d = feature.properties.date
    return d && new Date(d).getTime() <= currentTimestamp
  })

  // 2. 绘制点 (Events)
  if (layerGroups.value.events) {
    layerGroups.value.events.clearLayers()
    
    const geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleEvents }, {
      pointToLayer: (feature, latlng) => {
        const type = feature.properties.type
        let color = '#6b7280'
        if (type === 'battle') color = '#dc2626'
        else if (type === 'city') color = '#2563eb'
        else if (type === 'camp') color = '#16a34a'

        return L.circleMarker(latlng, {
          radius: 6,
          fillColor: color,
          color: '#ffffff',
          weight: 1,
          opacity: 1,
          fillOpacity: 1
        })
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties
        layer.bindPopup(`<strong>${p.name}</strong><br>${p.date}<br>${p.type}`)
      }
    })
    layerGroups.value.events.addLayer(geoJsonLayer)
  }

  // 3. 绘制连线 (Trajectory) - 连接所有可见的点
  if (layerGroups.value.trajectory) {
    layerGroups.value.trajectory.clearLayers()

    if (visibleEvents.length > 1) {
      // 提取坐标：GeoJSON 是 [lng, lat], Leaflet 需要 [lat, lng]
      const latlngs = visibleEvents.map(f => {
        const coords = f.geometry.coordinates
        return [coords[1], coords[0]]
      })

      const polyline = L.polyline(latlngs, {
        color: '#2563eb', // 轨迹颜色
        weight: 3,
        opacity: 0.8,
        lineJoin: 'round',
        dashArray: '1, 4', // 虚线样式，可选
        dashOffset: '0'
      })
      
      layerGroups.value.trajectory.addLayer(polyline)

      // 可选：视角跟随最新的点
      // const lastPoint = latlngs[latlngs.length - 1]
      // map.value.panTo(lastPoint, { animate: true, duration: 0.5 })
    }
  }
}

// 辅助功能：图层切换
const toggleMapLayerVisibility = (layerId, visible) => {
  if (!map.value) return
  const group = mapLayerGroups.value[layerId]
  if (!group) return

  if (visible) {
    if (!map.value.hasLayer(group)) map.value.addLayer(group)
  } else {
    if (map.value.hasLayer(group)) map.value.removeLayer(group)
  }
}

// 监听 Store 的图层显隐设置
watch(() => mapStore.visibleLayers, (newLayers) => {
    // 处理动态图层的显隐
    Object.keys(layerGroups.value).forEach(key => {
        const layer = layerGroups.value[key]
        if(!layer) return
        if (newLayers.includes(key)) {
            if (!map.value.hasLayer(layer)) map.value.addLayer(layer)
        } else {
            if (map.value.hasLayer(layer)) map.value.removeLayer(layer)
        }
    })
}, { deep: true })

onUnmounted(() => {
  if (map.value) map.value.remove()
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  background-color: #f8fafc; /* 设置一个浅色背景，避免地图加载前的空白 */
}
</style>