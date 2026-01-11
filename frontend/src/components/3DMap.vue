<template>
  <div class="map-3d-container">
    <!-- 3D渲染容器 -->
    <div ref="canvasContainer" class="canvas-container"></div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载3D地图中...</span>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-overlay">
      <span>⚠️ {{ error }}</span>
      <button @click="initMap" class="retry-btn">重试</button>
    </div>

    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="control-group">
        <label>视角:</label>
        <button @click="resetCamera" class="control-btn">重置</button>
      </div>
      <div class="control-group">
        <label>图层:</label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="layers.events" @change="updateLayers" />
          <span>事件</span>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="layers.movements" @change="updateLayers" />
          <span>行军</span>
        </label>
      </div>
    </div>

    <!-- 信息面板 -->
    <div class="info-panel">
      <div class="info-item">
        <span class="info-label">事件数:</span>
        <span class="info-value">{{ eventCount }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">行军路线:</span>
        <span class="info-value">{{ movementCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { useMapStore } from '@/stores/map'
import { fetchEvents, fetchMovements } from '@/services/api'

const mapStore = useMapStore()
const canvasContainer = ref(null)
const loading = ref(true)
const error = ref(null)

// Three.js 对象
let scene, camera, renderer, controls
let eventMarkers = []
let movementLines = []

// 图层控制
const layers = ref({
  events: true,
  movements: true
})

// 统计信息
const eventCount = ref(0)
const movementCount = ref(0)

// 经纬度转换为3D坐标
const latLonToVector3 = (lat, lon, radius = 100) => {
  const phi = (90 - lat) * (Math.PI / 180)
  const theta = (lon + 180) * (Math.PI / 180)

  const x = -(radius * Math.sin(phi) * Math.cos(theta))
  const z = radius * Math.sin(phi) * Math.sin(theta)
  const y = radius * Math.cos(phi)

  return new THREE.Vector3(x, y, z)
}

// 初始化Three.js场景
const initThreeScene = () => {
  if (!canvasContainer.value) return

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a0e27)

  // 创建相机
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 10000)
  camera.position.set(0, 0, 300)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  canvasContainer.value.appendChild(renderer.domElement)

  // 添加轨道控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 150
  controls.maxDistance = 500

  // 添加环境光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  // 添加方向光
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(200, 200, 200)
  scene.add(directionalLight)

  // 创建地球
  createEarth()

  // 开始动画循环
  animate()
}

// 创建地球
const createEarth = () => {
  const geometry = new THREE.SphereGeometry(100, 64, 64)
  const material = new THREE.MeshPhongMaterial({
    color: 0x2d5a8c,
    emissive: 0x112244,
    shininess: 10,
    transparent: true,
    opacity: 0.9
  })
  const earth = new THREE.Mesh(geometry, material)
  scene.add(earth)

  // 添加网格线
  const wireframe = new THREE.WireframeGeometry(geometry)
  const line = new THREE.LineSegments(wireframe)
  line.material.color.setHex(0x4a90e2)
  line.material.opacity = 0.2
  line.material.transparent = true
  scene.add(line)
}

// 动画循环
const animate = () => {
  requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

// 加载事件数据
const loadEvents = async () => {
  try {
    const data = await fetchEvents({ projection: mapStore.projection })
    console.log('3D Events loaded:', data.features.length)

    eventCount.value = data.features.length
    renderEvents(data.features)
  } catch (err) {
    console.error('Error loading events:', err)
  }
}

// 渲染事件标记
const renderEvents = (features) => {
  // 清除旧标记
  eventMarkers.forEach(marker => scene.remove(marker))
  eventMarkers = []

  features.forEach(feature => {
    const coords = feature.geometry.coordinates
    const lat = coords[1]
    const lon = coords[0]

    const position = latLonToVector3(lat, lon, 102)

    // 创建标记
    const geometry = new THREE.SphereGeometry(1.5, 16, 16)
    const material = new THREE.MeshBasicMaterial({
      color: 0xff4444,
      transparent: true,
      opacity: 0.8
    })
    const marker = new THREE.Mesh(geometry, material)
    marker.position.copy(position)

    scene.add(marker)
    eventMarkers.push(marker)
  })
}

// 加载行军路线数据
const loadMovements = async () => {
  try {
    const data = await fetchMovements({ projection: mapStore.projection })
    console.log('3D Movements loaded:', data.features.length)

    movementCount.value = data.features.length
    renderMovements(data.features)
  } catch (err) {
    console.error('Error loading movements:', err)
  }
}

// 渲染行军路线
const renderMovements = (features) => {
  // 清除旧路线
  movementLines.forEach(line => scene.remove(line))
  movementLines = []

  features.forEach(feature => {
    if (feature.geometry.type !== 'LineString') return

    const coords = feature.geometry.coordinates
    const points = []

    coords.forEach(coord => {
      const lat = coord[1]
      const lon = coord[0]
      const position = latLonToVector3(lat, lon, 101)
      points.push(position)
    })

    // 创建路线
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({
      color: 0x44aaff,
      linewidth: 2,
      transparent: true,
      opacity: 0.6
    })
    const line = new THREE.Line(geometry, material)

    scene.add(line)
    movementLines.push(line)
  })
}

// 更新图层显示
const updateLayers = () => {
  eventMarkers.forEach(marker => {
    marker.visible = layers.value.events
  })
  movementLines.forEach(line => {
    line.visible = layers.value.movements
  })
}

// 重置相机
const resetCamera = () => {
  camera.position.set(0, 0, 300)
  controls.target.set(0, 0, 0)
  controls.update()
}

// 初始化地图
const initMap = async () => {
  loading.value = true
  error.value = null

  try {
    initThreeScene()
    await Promise.all([loadEvents(), loadMovements()])
  } catch (err) {
    error.value = '加载3D地图失败'
    console.error('Error initializing 3D map:', err)
  } finally {
    loading.value = false
  }
}

// 窗口大小调整
const handleResize = () => {
  if (!canvasContainer.value || !camera || !renderer) return

  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 生命周期钩子
onMounted(() => {
  console.log('3DMap mounted')
  initMap()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<style scoped>
.map-3d-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #0a0e27;
}

.canvas-container {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 14, 39, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  color: white;
  font-size: 18px;
  z-index: 100;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(239, 68, 68, 0.95);
  color: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.retry-btn {
  padding: 10px 20px;
  background: white;
  color: #ef4444;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: #f8fafc;
}

.control-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.control-btn {
  padding: 6px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #2563eb;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
}

.info-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.info-label {
  font-size: 13px;
  color: #64748b;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}
</style>
