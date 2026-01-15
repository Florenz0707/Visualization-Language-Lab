<template>
  <div class="napoleon-container">
    <div id="loading" v-show="loading">正在加载...</div>
    <button id="view-btn" @click="toggleViewMode">切换视图 2D/3D</button>

    <div id="ui-layer">
      <h3>1812 俄法战争</h3>
      <div class="legend-item">
        <span style="color:#d63031; font-weight:bold;">—</span> 进攻 (10.10前)
      </div>
      <div class="legend-item">
        <span style="color:#222222; font-weight:bold;">—</span> 撤退 (10.10后)
      </div>
      <div class="legend-item">
        <div class="dot" style="background:#ffff00; border:1px solid #000;"></div> 选中高亮
      </div>
      <div style="font-size:11px; margin-top:10px; color:#555;">
        * 点击箭头显示地名<br>
        * 点击路线进行分析
      </div>
    </div>

    <div id="timeline-container">
      <div id="date-display">{{ currentDate }}</div>
      <input
        type="range"
        id="time-slider"
        :min="0"
        :max="timelineData.length - 1"
        v-model="currentTimeIndex"
        @input="onTimelineChange"
      >
    </div>

    <div id="analysis-panel" :class="{ active: showAnalysisPanel }">
      <div class="panel-header">
        <h3>📜 AI 战况分析</h3>
        <button class="close-btn" @click="showAnalysisPanel = false">×</button>
      </div>
      <div id="analysis-content" v-html="analysisContent"></div>
    </div>

    <div ref="canvasContainer" class="canvas-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer'
import { analyzeRoute } from '../services/api'

// Refs
const canvasContainer = ref(null)
const loading = ref(true)
const currentDate = ref('1812-06-24')
const currentTimeIndex = ref(0)
const timelineData = ref([])
const showAnalysisPanel = ref(false)
const analysisContent = ref('<p style="text-align:center; color:#666;">点击地图上的路线以查看分析。</p>')

// Three.js variables
let scene, camera, renderer, labelRenderer, controls
let terrainMesh
let routeMeshes = []
let arrowMeshes = []
let is2DMode = false
let selectedRoute = null
let animationFrameId = null

// Raycaster for interaction
const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

const CONFIG = {
  worldWidth: 250,
  worldHeight: 100,
  heightScale: 25,
  waterLevel: 2.0,
  colors: {
    sky: 0xaaccff,
    water: 0x3d85c6,
    riverLine: 0x2c6ba0,
    city: 0x44ff44,
    capital: 0xff0000,
    battle: 0xffaa00,
    attack: 0xd63031,
    retreat: 0x2d3436,
    highlight: 0xffff00
  },
  camera3D: { x: 0, y: 100, z: 120 },
  camera2D: { x: 0, y: 250, z: 0 }
}

onMounted(() => {
  initThreeJS()
  loadResources()
  window.addEventListener('resize', onResize)
  window.addEventListener('click', onMouseClick)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('click', onMouseClick)
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  if (renderer) {
    renderer.dispose()
  }
  if (labelRenderer && labelRenderer.domElement) {
    labelRenderer.domElement.remove()
  }
})

// Initialize Three.js scene
function initThreeJS() {
  scene = new THREE.Scene()
  scene.background = new THREE.Color(CONFIG.colors.sky)
  scene.fog = new THREE.Fog(CONFIG.colors.sky, 50, 400)

  camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    1,
    1000
  )
  camera.position.set(CONFIG.camera3D.x, CONFIG.camera3D.y, CONFIG.camera3D.z)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  canvasContainer.value.appendChild(renderer.domElement)

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(window.innerWidth, window.innerHeight)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0px'
  labelRenderer.domElement.style.pointerEvents = 'none'
  canvasContainer.value.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI / 2 - 0.1

  const sun = new THREE.DirectionalLight(0xffffee, 1.2)
  sun.position.set(-50, 100, 50)
  sun.castShadow = true
  sun.shadow.mapSize.width = 2048
  sun.shadow.mapSize.height = 2048
  sun.shadow.camera.left = -150
  sun.shadow.camera.right = 150
  sun.shadow.camera.top = 150
  sun.shadow.camera.bottom = -150
  scene.add(sun)
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))

  animate()
}

// Load resources
async function loadResources() {
  try {
    const texLoader = new THREE.TextureLoader()
    const [heightMap, textureMap, gameData] = await Promise.all([
      new Promise((resolve) => texLoader.load('/assets/heightmap.png', resolve)),
      new Promise((resolve) => texLoader.load('/assets/texture.png', resolve, undefined, () => resolve(null))),
      fetch('/game_data.json').then(r => r.json())
    ])

    loading.value = false
    buildWorld(heightMap, textureMap, gameData)
  } catch (e) {
    console.error('Failed to load resources:', e)
    loading.value = false
  }
}

// Build the 3D world
function buildWorld(heightMap, textureMap, data) {
  const mat = new THREE.MeshStandardMaterial({
    color: textureMap ? 0xffffff : 0x5da668,
    map: textureMap || null,
    displacementMap: heightMap,
    displacementScale: CONFIG.heightScale,
    roughness: 0.8
  })

  const geo = new THREE.PlaneGeometry(CONFIG.worldWidth, CONFIG.worldHeight, 256, 256)
  terrainMesh = new THREE.Mesh(geo, mat)
  terrainMesh.rotation.x = -Math.PI / 2
  terrainMesh.receiveShadow = true
  terrainMesh.castShadow = true
  scene.add(terrainMesh)

  const water = new THREE.Mesh(
    new THREE.PlaneGeometry(CONFIG.worldWidth, CONFIG.worldHeight),
    new THREE.MeshStandardMaterial({
      color: CONFIG.colors.water,
      transparent: true,
      opacity: 0.8
    })
  )
  water.rotation.x = -Math.PI / 2
  water.position.y = CONFIG.waterLevel
  scene.add(water)

  setTimeout(() => drawVectors(data), 50)
}

// Draw vectors (routes, rivers, cities)
function drawVectors(data) {
  if (data.timeline) {
    timelineData.value = data.timeline
  }

  if (data.rivers) {
    data.rivers.forEach(pts => drawLine(pts, CONFIG.colors.riverLine))
  }

  if (data.routes) {
    data.routes.forEach(route => {
      const dateStr = timelineData.value[route.date_idx]
      const isAttack = dateStr ? (dateStr < "1812-10-10") : true

      const mesh = createRouteTube(
        route.path,
        isAttack ? CONFIG.colors.attack : CONFIG.colors.retreat,
        isAttack ? 0.6 : 0.3
      )

      if (mesh) {
        mesh.visible = false
        mesh.userData = {
          dateIdx: route.date_idx,
          type: isAttack ? '进攻' : '撤退',
          isRoute: true
        }
        routeMeshes.push(mesh)
      }
    })
    updateRouteVisibility(0)
  }

  if (data.cities) {
    data.cities.forEach(city => placeCity(city, data.routes))
  }
}

// Create route tube
function createRouteTube(points, color, radius) {
  if (points.length < 2) return null
  const vecs = points.map(p => new THREE.Vector3(
    p[0],
    Math.max(p[1] * CONFIG.heightScale, CONFIG.waterLevel) + 1.0,
    p[2]
  ))
  const curve = new THREE.CatmullRomCurve3(vecs)
  const geo = new THREE.TubeGeometry(curve, points.length * 2, radius, 8, false)
  const mat = new THREE.MeshStandardMaterial({ color: color, roughness: 0.4 })
  const mesh = new THREE.Mesh(geo, mat)
  mesh.castShadow = true
  scene.add(mesh)
  return mesh
}

// Draw line
function drawLine(points, color) {
  const v = []
  points.forEach(p => {
    v.push(p[0], Math.max(p[1] * CONFIG.heightScale, CONFIG.waterLevel) + 0.2, p[2])
  })
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(v, 3))
  scene.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color: color, linewidth: 2 })))
}

// Place city
function placeCity(city, routes) {
  const y = Math.max(city.ny * CONFIG.heightScale, CONFIG.waterLevel)
  const grp = new THREE.Group()
  grp.position.set(city.x, y, city.z)

  let color = CONFIG.colors.city
  let scale = 1.0

  const dateStr = getDateForLocation(city.x, city.z, routes)
  if (dateStr) {
    if (dateStr < "1812-10-10") {
      color = CONFIG.colors.attack
    } else {
      color = 0x222222
    }
  }

  if (city.t === 'capital') scale = 1.5
  if (city.t === 'battle') scale = 1.3

  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(0.2 * scale, 0.5 * scale, 1.2 * scale, 6),
    new THREE.MeshStandardMaterial({ color: 0x888888 })
  )
  mesh.position.y = 0.6 * scale
  mesh.castShadow = true
  grp.add(mesh)

  const div = document.createElement('div')
  div.className = city.t === 'battle' ? 'city-label battle-label' : 'city-label'
  div.textContent = city.n + (dateStr ? ` (${dateStr})` : "")
  div.style.opacity = '0'
  div.style.transition = 'opacity 0.3s'

  const label = new CSS2DObject(div)
  label.position.set(0, 3 * scale, 0)
  grp.add(label)

  createArrow(grp, color, label)
  scene.add(grp)
}

// Create arrow
function createArrow(grp, color, labelObj) {
  const arrowMat = new THREE.MeshLambertMaterial({ color: color, emissive: 0x222222 })
  const arrow = new THREE.Mesh(new THREE.ConeGeometry(0.6, 1.5, 8), arrowMat)
  arrow.rotation.x = Math.PI
  arrow.userData = { label: labelObj }
  grp.add(arrow)
  arrowMeshes.push({
    mesh: arrow,
    baseY: 5,
    speed: 2 + Math.random(),
    offset: Math.random() * Math.PI
  })
}

// Get date for location
function getDateForLocation(x, z, routes) {
  let minDist = Infinity
  let closestRoute = null

  if (!routes) return null

  routes.forEach(route => {
    if (!route.path) return
    route.path.forEach(pt => {
      const dx = pt[0] - x
      const dz = pt[2] - z
      const dist = dx * dx + dz * dz
      if (dist < minDist) {
        minDist = dist
        closestRoute = route
      }
    })
  })

  if (minDist > 400) return null

  if (closestRoute && timelineData.value[closestRoute.date_idx]) {
    return timelineData.value[closestRoute.date_idx]
  }
  return null
}

// Update route visibility based on timeline
function updateRouteVisibility(idx) {
  routeMeshes.forEach(m => {
    m.visible = m.userData.dateIdx === idx
  })
  if (selectedRoute && !selectedRoute.visible) {
    selectedRoute.material.emissive.setHex(0x000000)
    selectedRoute = null
  }
}

// Unmap coordinates
function unmapCoords(x, z) {
  const bounds = { min_lon: 20.0, max_lon: 45.0, min_lat: 50.0, max_lat: 60.0 }
  const nx = (x / CONFIG.worldWidth) + 0.5
  const lon = nx * (bounds.max_lon - bounds.min_lon) + bounds.min_lon
  const ny = -(z / CONFIG.worldHeight) + 0.5
  const lat = ny * (bounds.max_lat - bounds.min_lat) + bounds.min_lat
  return { lon, lat }
}

// Mouse click handler
function onMouseClick(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1
  raycaster.setFromCamera(mouse, camera)

  const visibleRoutes = routeMeshes.filter(m => m.visible)
  const routeIntersects = raycaster.intersectObjects(visibleRoutes)

  if (routeIntersects.length > 0) {
    const hit = routeIntersects[0]
    highlightRoute(hit.object)
    triggerAnalysis(hit.object, hit.point)
    return
  }

  const arrowIntersects = raycaster.intersectObjects(arrowMeshes.map(a => a.mesh))
  if (arrowIntersects.length > 0) {
    const hit = arrowIntersects[0]
    const arrowUserData = hit.object.userData
    if (arrowUserData && arrowUserData.label) {
      const style = arrowUserData.label.element.style
      style.opacity = style.opacity === '1' ? '0' : '1'
    }
  }
}

// Highlight route
function highlightRoute(mesh) {
  if (selectedRoute) {
    selectedRoute.material.emissive.setHex(0x000000)
  }
  selectedRoute = mesh
  selectedRoute.material.emissive.setHex(CONFIG.colors.highlight)
}

// Trigger AI analysis
async function triggerAnalysis(mesh, point) {
  showAnalysisPanel.value = true
  analysisContent.value = '<div class="loading-text">📡 正在连接后端服务...<br>分析地形与战略态势...</div>'

  const coords = unmapCoords(point.x, point.z)
  const dateStr = timelineData.value[mesh.userData.dateIdx] || "1812年"
  const heightVal = point.y / CONFIG.heightScale

  let terrain = "平原"
  if (heightVal > 0.4) terrain = "丘陵/高地"
  if (heightVal > 0.8) terrain = "山脉阻隔"

  try {
    const result = await analyzeRoute({
      lat: coords.lat,
      lon: coords.lon,
      date: dateStr,
      type: mesh.userData.type,
      terrain_hint: `${terrain} (海拔系数 ${heightVal.toFixed(2)})`
    })

    analysisContent.value = `
      <div style="font-size:12px; color:#999; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">
        📍 ${coords.lat.toFixed(2)}°N, ${coords.lon.toFixed(2)}°E <br>
        📅 ${dateStr} | 法军${mesh.userData.type}
      </div>
      <div style="font-family:'Times New Roman', serif; line-height:1.6; color:#2c3e50; text-align:justify;">
        ${result.analysis.replace(/\n/g, '<br>')}
      </div>
    `
  } catch (e) {
    console.error('Analysis failed:', e)
    analysisContent.value = '<p style="color:red">分析服务连接失败，请确认后端服务已运行。</p>'
  }
}

// Toggle view mode
function toggleViewMode() {
  is2DMode = !is2DMode
  const targetPos = is2DMode ? CONFIG.camera2D : CONFIG.camera3D

  const startPos = { ...camera.position }
  const duration = 1500
  const startTime = Date.now()

  function animateCamera() {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2

    camera.position.x = startPos.x + (targetPos.x - startPos.x) * eased
    camera.position.y = startPos.y + (targetPos.y - startPos.y) * eased
    camera.position.z = startPos.z + (targetPos.z - startPos.z) * eased
    camera.lookAt(0, 0, 0)

    if (progress < 1) {
      requestAnimationFrame(animateCamera)
    } else {
      if (is2DMode) {
        controls.enableRotate = false
        controls.screenSpacePanning = true
        scene.fog.density = 0
      } else {
        controls.enableRotate = true
        controls.screenSpacePanning = false
        scene.fog.density = 0.002
      }
      controls.reset()
    }
  }

  animateCamera()
}

// Timeline change handler
function onTimelineChange() {
  const idx = parseInt(currentTimeIndex.value)
  if (timelineData.value[idx]) {
    currentDate.value = timelineData.value[idx]
    updateRouteVisibility(idx)
  }
}

// Window resize handler
function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
  labelRenderer.setSize(window.innerWidth, window.innerHeight)
}

// Animation loop
function animate() {
  animationFrameId = requestAnimationFrame(animate)

  controls.update()

  const t = Date.now() * 0.003
  arrowMeshes.forEach(i => {
    i.mesh.position.y = i.baseY + Math.sin(t * i.speed + i.offset)
    i.mesh.rotation.y += 0.02
  })

  renderer.render(scene, camera)
  labelRenderer.render(scene, camera)
}
</script>

<style scoped>
.napoleon-container {
  margin: 0;
  overflow: hidden;
  background-color: #aaccff;
  font-family: 'Segoe UI', sans-serif;
  position: relative;
  width: 100vw;
  height: 100vh;
}

.canvas-container {
  width: 100%;
  height: 100%;
}

#loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 24px;
  background: rgba(0, 0, 0, 0.5);
  padding: 20px;
  border-radius: 10px;
  z-index: 200;
}

#ui-layer {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.9);
  padding: 15px;
  border-radius: 8px;
  pointer-events: none;
  z-index: 10;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  margin-top: 5px;
  font-size: 13px;
  color: #333;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
}

#timeline-container {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  background: rgba(255, 255, 255, 0.95);
  padding: 15px 30px;
  border-radius: 30px;
  text-align: center;
  z-index: 10;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

#date-display {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
  font-family: 'Times New Roman', serif;
}

#time-slider {
  width: 100%;
  cursor: pointer;
  margin: 10px 0;
}

#view-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 10px 20px;
  background: #2c3e50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  z-index: 100;
  font-weight: bold;
}

#view-btn:hover {
  background: #34495e;
}

#analysis-panel {
  position: absolute;
  top: 80px;
  right: -350px;
  width: 320px;
  max-height: 70vh;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  box-shadow: -5px 5px 20px rgba(0, 0, 0, 0.2);
  transition: right 0.4s ease;
  z-index: 100;
}

#analysis-panel.active {
  right: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.close-btn {
  cursor: pointer;
  border: none;
  background: none;
  font-size: 18px;
}

:deep(.city-label) {
  color: white;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  pointer-events: none;
}

:deep(.battle-label) {
  border: 1px solid gold;
  color: gold;
  background: rgba(0, 0, 0, 0.8);
}

.loading-text {
  text-align: center;
  color: #666;
  padding: 20px;
}
</style>
