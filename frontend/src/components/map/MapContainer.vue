<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useMapStore } from '@/stores/map'
import { fetchEvents, fetchMovements, fetchTerritories } from '@/services/api'

const mapContainer = ref(null)
const map = ref(null)
const mapStore = useMapStore()

// Layer groups
const layerGroups = ref({
  events: null,
  movements: null,
  territories: null
})

onMounted(async () => {
  // Initialize Leaflet map
  map.value = L.map(mapContainer.value, {
    center: [55.7558, 37.6173], // Moscow [lat, lng]
    zoom: 5,
    zoomControl: true
  })

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value)

  mapStore.setMapInstance(map.value)

  // Load data layers
  await loadLayers()
})

const loadLayers = async () => {
  try {
    // Load events
    const eventsData = await fetchEvents({
      projection: mapStore.projection
    })

    layerGroups.value.events = L.geoJSON(eventsData, {
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
          fillOpacity: 0.8
        })
      },
      onEachFeature: (feature, layer) => {
        if (feature.properties) {
          const props = feature.properties
          layer.bindPopup(`
            <strong>${props.name || 'Unknown'}</strong><br>
            Type: ${props.type || 'N/A'}<br>
            Date: ${props.date || 'N/A'}
          `)
        }
      }
    }).addTo(map.value)

  } catch (error) {
    console.error('Error loading events:', error)
  }

  try {
    // Load movements
    const movementsData = await fetchMovements({
      projection: mapStore.projection,
      zoom: Math.round(map.value.getZoom())
    })

    layerGroups.value.movements = L.geoJSON(movementsData, {
      style: (feature) => {
        const direction = feature.properties.direction
        const survivors = feature.properties.survivors || 10000

        let color = '#6b7280'
        if (direction === 'advance') color = '#3b82f6'
        else if (direction === 'retreat') color = '#ef4444'

        // Calculate line width based on survivors
        let weight = 2
        if (survivors > 100000) weight = 8
        else if (survivors > 50000) weight = 5
        else if (survivors > 10000) weight = 3

        return {
          color: color,
          weight: weight,
          opacity: 0.7
        }
      },
      onEachFeature: (feature, layer) => {
        if (feature.properties) {
          const props = feature.properties
          layer.bindPopup(`
            <strong>${props.unit || 'Unknown Unit'}</strong><br>
            Direction: ${props.direction || 'N/A'}<br>
            Survivors: ${props.survivors ? props.survivors.toLocaleString() : 'N/A'}
          `)
        }
      }
    }).addTo(map.value)

  } catch (error) {
    console.error('Error loading movements:', error)
  }

  try {
    // Load territories
    const territoriesData = await fetchTerritories({
      projection: mapStore.projection
    })

    layerGroups.value.territories = L.geoJSON(territoriesData, {
      style: (feature) => {
        const faction = feature.properties.faction
        let color = '#6b7280'

        if (faction === 'french') color = '#3b82f6'
        else if (faction === 'russian') color = '#ef4444'

        return {
          fillColor: color,
          fillOpacity: 0.2,
          color: color,
          weight: 1,
          opacity: 0.5
        }
      },
      onEachFeature: (feature, layer) => {
        if (feature.properties) {
          const props = feature.properties
          layer.bindPopup(`
            <strong>${props.name || 'Territory'}</strong><br>
            Faction: ${props.faction || 'N/A'}
          `)
        }
      }
    }).addTo(map.value)

  } catch (error) {
    console.error('Error loading territories:', error)
  }
}

// Watch for layer visibility changes
watch(() => mapStore.visibleLayers, (newLayers) => {
  if (!map.value) return

  Object.entries(layerGroups.value).forEach(([key, layerGroup]) => {
    if (layerGroup) {
      if (newLayers.includes(key)) {
        if (!map.value.hasLayer(layerGroup)) {
          map.value.addLayer(layerGroup)
        }
      } else {
        if (map.value.hasLayer(layerGroup)) {
          map.value.removeLayer(layerGroup)
        }
      }
    }
  })
}, { deep: true })

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
