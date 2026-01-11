<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useMapStore } from '@/stores/map'
import { fetchEvents, fetchMovements, fetchTerritories, fetchFlows } from '@/services/api'

const mapContainer = ref(null)
const map = ref(null)
const mapStore = useMapStore()

// Layer groups
const layerGroups = ref({
  events: null,
  movements: null,
  territories: null,
  flows: null
})

// Map layer groups (countries, provinces, cities, rivers)
const mapLayerGroups = ref({
  countries: null,
  provinces: null,
  cities_major: null,
  rivers: null
})

// Store all data for filtering
const allData = ref({
  events: null,
  movements: null,
  territories: null,
  flows: null
})

onMounted(async () => {
  // Initialize Leaflet map
  map.value = L.map(mapContainer.value, {
    center: [55.0, 30.0], // Center between Poland and Moscow for horizontal view
    zoom: 4.5,
    zoomControl: true,
    minZoom: 3,
    maxZoom: 10
  })

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value)

  mapStore.setMapInstance(map.value)

  // Load data layers
  await loadLayers()

  // Load all map layers at startup
  await loadAllMapLayers()
})

const loadLayers = async () => {
  try {
    // Load events
    const eventsData = await fetchEvents({
      projection: mapStore.projection
    })

    // Store original data
    allData.value.events = eventsData

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

  try {
    // Load flows
    const flowsData = await fetchFlows({
      simplify: true,
      threshold: 0.01
    })

    allData.value.flows = flowsData

    layerGroups.value.flows = L.geoJSON(flowsData, {
      style: (feature) => {
        const eventsCount = feature.properties.events_count || 1

        // Calculate line width based on events count
        let weight = 3
        if (eventsCount > 10) weight = 6
        else if (eventsCount > 5) weight = 5
        else if (eventsCount > 2) weight = 4

        return {
          color: '#8b5cf6',
          weight: weight,
          opacity: 0.6,
          dashArray: '5, 5'
        }
      },
      onEachFeature: (feature, layer) => {
        if (feature.properties) {
          const props = feature.properties
          layer.bindPopup(`
            <strong>${props.unit || 'Flow'}</strong><br>
            Events: ${props.events_count || 'N/A'}<br>
            Period: ${props.start_date || 'N/A'} - ${props.end_date || 'N/A'}
          `)
        }
      }
    }).addTo(map.value)

  } catch (error) {
    console.error('Error loading flows:', error)
  }
}

// Load all map layers at startup
const loadAllMapLayers = async () => {
  const mapLayerTypes = ['countries', 'provinces', 'cities_major', 'rivers']

  for (const layerId of mapLayerTypes) {
    try {
      const response = await fetch(`http://localhost:9000/api/maps/${layerId}?simplify=false`)
      const data = await response.json()

      // Create layer but don't add to map yet
      const layer = L.geoJSON(data, {
        style: (feature) => {
          if (layerId === 'countries' || layerId === 'provinces') {
            return {
              fillColor: 'transparent',
              color: '#94a3b8',
              weight: layerId === 'countries' ? 2 : 1,
              opacity: 0.6
            }
          } else if (layerId === 'rivers') {
            return {
              color: '#3b82f6',
              weight: 1.5,
              opacity: 0.5
            }
          }
          return {}
        },
        pointToLayer: (feature, latlng) => {
          if (layerId === 'cities_major') {
            return L.circleMarker(latlng, {
              radius: 4,
              fillColor: '#f59e0b',
              color: '#fff',
              weight: 1,
              opacity: 1,
              fillOpacity: 0.7
            })
          }
        },
        onEachFeature: (feature, layer) => {
          if (feature.properties && feature.properties.name) {
            layer.bindPopup(`<strong>${feature.properties.name}</strong>`)
          }
        }
      })

      mapLayerGroups.value[layerId] = layer
    } catch (error) {
      console.error(`Error loading map layer ${layerId}:`, error)
    }
  }

  // Store toggle function in mapStore after all layers are loaded
  mapStore.setMapLayerToggleFunction(toggleMapLayerVisibility)
}

// Function to toggle map layer visibility
const toggleMapLayerVisibility = (layerId, visible) => {
  if (!map.value) return

  const layerGroup = mapLayerGroups.value[layerId]
  if (!layerGroup) return

  if (visible) {
    if (!map.value.hasLayer(layerGroup)) {
      map.value.addLayer(layerGroup)
    }
  } else {
    if (map.value.hasLayer(layerGroup)) {
      map.value.removeLayer(layerGroup)
    }
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

// Watch for time changes to filter data
watch(() => mapStore.currentTime, (newTime) => {
  filterDataByTime(newTime)
})

const filterDataByTime = (currentTime) => {
  if (!map.value || !allData.value.events) return

  const currentTimestamp = currentTime.getTime()

  // Filter events by date
  if (layerGroups.value.events) {
    map.value.removeLayer(layerGroups.value.events)
  }

  const filteredEvents = {
    ...allData.value.events,
    features: allData.value.events.features.filter(feature => {
      const eventDate = feature.properties.date
      if (!eventDate) return true
      const eventTimestamp = new Date(eventDate).getTime()
      return eventTimestamp <= currentTimestamp
    })
  }

  layerGroups.value.events = L.geoJSON(filteredEvents, {
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
  })

  if (mapStore.visibleLayers.includes('events')) {
    layerGroups.value.events.addTo(map.value)
  }
}

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
