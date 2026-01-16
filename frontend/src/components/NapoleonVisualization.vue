<template>
  <div class="napoleon-container">
    <div id="loading" v-show="loading">正在加载...</div>
    
    <button id="view-btn" @click="toggleViewMode">
      {{ is2DMode ? '切换到 3D 战术视图' : '切换到 2D 战略视图' }}
    </button>

    <div id="ui-layer">
      <h3>1812 俄法战争</h3>
      
      <div class="legend-section">
        <div class="legend-title">战略阶段 (勾选筛选显示)</div>
        <div class="legend-item clickable">
          <label>
            <input type="checkbox" v-model="showAllAttack">
            <span class="icon line-attack"></span> 显示所有进攻路线
          </label>
        </div>
        <div class="legend-item clickable">
          <label>
            <input type="checkbox" v-model="showAllRetreat">
            <span class="icon line-retreat"></span> 显示所有撤退路线
          </label>
        </div>
      </div>

      <div class="legend-section">
        <div class="legend-title">关键地点 (箭头类型)</div>
        <div class="legend-item"><span class="icon dot-capital"></span> 关键战役</div>
        <div class="legend-item"><span class="icon dot-battle"></span> 首都/重镇</div>
        <div class="legend-item"><span class="icon dot-city"></span> 事件（降雪，焦土政策等）</div>
      </div>

      <div class="legend-section">
        <div class="legend-item"><span class="icon highlight-box"></span> 选中高亮</div>
      </div>

      <div class="legend-section chart-section">
        <div class="chart-header">
          <span class="chart-label" style="color:#3498db;">■ 法军兵力</span>
          <span id="french-val" class="chart-value">--</span>
        </div>
        <div id="chart-french" class="mini-chart"></div>

        <div class="chart-header">
          <span class="chart-label" style="color:#2ecc71;">■ 俄军兵力</span>
          <span id="russian-val" class="chart-value">--</span>
        </div>
        <div id="chart-russian" class="mini-chart"></div>

        <div class="chart-header">
          <span class="chart-label" style="color:#9b59b6;">■ 兵力对比 (法/俄)</span>
          <span id="ratio-val" class="chart-value">--</span>
        </div>
        <div id="chart-ratio" class="mini-chart"></div>
      </div>

      <div class="tips">
        * 勾选上方复选框可查看完整路线<br>
        * 拖动 D3 时间轴跳转日期<br>
        * 点击地图上的路线查看地形与分析
      </div>
    </div>

    <div id="timeline-container">
      <div id="date-display">
        {{ currentDate }}
        <div class="event-name">{{ currentEventName }}</div>
      </div>
      <div id="d3-timeline" ref="d3TimelineRef"></div>
    </div>

    <div id="analysis-panel" :class="{ active: showAnalysisPanel }">
      <div class="panel-header">
        <h3>📜 AI 战况分析</h3>
        <button class="close-btn" @click="showAnalysisPanel = false">×</button>
      </div>
      <div id="analysis-content" v-html="analysisContent"></div>
      <div id="d3-elevation-chart" ref="elevationChartRef"></div>
    </div>

    <div ref="canvasContainer" class="canvas-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import * as d3 from 'd3'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer'
import { analyzeRoute } from '../services/api'

// --- Refs & State ---
const canvasContainer = ref(null)
const d3TimelineRef = ref(null)
const elevationChartRef = ref(null)

const loading = ref(true)
const currentDate = ref('1812-06-24')
const currentEventName = ref('')
const currentTimeIndex = ref(0)
const timelineData = ref([])
const showAnalysisPanel = ref(false)
const analysisContent = ref('<p style="text-align:center; color:#666;">点击地图上的路线以查看分析。</p>')
const is2DMode = ref(false)

// --- 新增：筛选状态 ---
const showAllAttack = ref(false)
const showAllRetreat = ref(false)

// --- Data ---
let troopsData = []

// --- Three.js Variables ---
let scene, camera, renderer, labelRenderer, controls
let terrainMesh
let routeMeshes = []
let arrowMeshes = []
let selectedRoute = null
let animationFrameId = null

// --- D3 Variables ---
let d3Handle = null
let d3XScale = null
let d3Dates = []

// 图表对象存储
const charts = {
  french: { svg: null, indicator: null, xScale: null, yScale: null },
  russian: { svg: null, indicator: null, xScale: null, yScale: null },
  ratio: { svg: null, indicator: null, xScale: null, yScale: null }
}

// --- Raycaster ---
const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

// --- Config ---
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

// --- Lifecycle ---
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

// --- Watchers ---
watch(currentTimeIndex, (newVal) => {
  if (timelineData.value[newVal]) {
    currentDate.value = timelineData.value[newVal]
    if (troopsData[newVal]) {
      currentEventName.value = troopsData[newVal].name || ''
    }
    updateRouteVisibility(newVal) // 更新路线显示
    updateD3HandlePosition(newVal)
    updateAllChartsIndicator(newVal)
  }
})

// 新增：监听筛选框变化，立即刷新路线
watch([showAllAttack, showAllRetreat], () => {
  updateRouteVisibility(currentTimeIndex.value)
})

// --- Data Processing ---
function processTroopsData(gameData) {
  const parseDate = d3.timeParse("%Y-%m-%d")
  const nodesWithTroops = gameData.cities.filter(c => c.french_troops !== undefined)
  
  troopsData = gameData.timeline.map((dateStr, i) => {
    const node = nodesWithTroops[i]
    return {
      date: parseDate(dateStr),
      french: node ? node.french_troops : 0,
      russian: node ? node.russian_troops : 0,
      ratio: node ? node.force_ratio : 0,
      name: node ? node.n : '',
      idx: i
    }
  })
}

// --- D3 Logic ---
function initD3Timeline(gameData) {
  const timeline = gameData.timeline
  if (!d3TimelineRef.value) return

  const container = d3TimelineRef.value
  const width = container.clientWidth
  const height = container.clientHeight
  const margin = { top: 10, right: 30, bottom: 40, left: 30 }

  d3.select(container).html("")

  const svg = d3.select(container)
    .append("svg")
    .attr("width", width)
    .attr("height", height)

  const parseDate = d3.timeParse("%Y-%m-%d")
  d3Dates = timeline.map(d => parseDate(d))

  d3XScale = d3.scaleTime()
    .domain(d3.extent(d3Dates))
    .range([margin.left, width - margin.right])

  const xAxis = d3.axisBottom(d3XScale)
    .ticks(5)
    .tickFormat(d3.timeFormat("%b %d"))

  svg.append("g")
    .attr("transform", `translate(0, ${height / 2 })`)
    .call(xAxis)
    .select(".domain").remove()

  // 事件名称文本
  const labeledData = troopsData.filter(d => d.name)
  svg.append("g")
    .attr("class", "event-labels")
    .selectAll("text")
    .data(labeledData)
    .enter()
    .append("text")
    .text(d => d.name)
    .attr("x", d => d3XScale(d.date))
    .attr("y", height / 2 + 15)
    .attr("transform", d => `rotate(30, ${d3XScale(d.date)}, ${height / 2 + 15})`)
    .style("text-anchor", "start")
    .style("font-size", "9px")
    .style("fill", "#666")
    .style("font-family", "Arial, sans-serif")
    .style("cursor", "pointer")
    .on("click", (event, d) => {
        currentTimeIndex.value = d.idx;
        if(d3Handle) {
             d3Handle.transition().duration(200).attr("cx", d3XScale(d.date))
        }
    })

  const retreatDate = parseDate("1812-10-18")

  svg.append("line")
    .attr("x1", d3XScale(d3Dates[0]))
    .attr("y1", height / 2)
    .attr("x2", d3XScale(retreatDate))
    .attr("y2", height / 2)
    .attr("stroke", "#d63031")
    .attr("stroke-width", 6)
    .attr("stroke-linecap", "round")
    .attr("opacity", 0.6)

  svg.append("line")
    .attr("x1", d3XScale(retreatDate))
    .attr("y1", height / 2)
    .attr("x2", d3XScale(d3Dates[d3Dates.length - 1]))
    .attr("y2", height / 2)
    .attr("stroke", "#2d3436")
    .attr("stroke-width", 6)
    .attr("stroke-linecap", "round")
    .attr("opacity", 0.8)

  const sliderGroup = svg.append("g").attr("class", "slider-group")

  d3Handle = sliderGroup.append("circle")
    .attr("class", "slider-handle")
    .attr("r", 8)
    .attr("cy", height / 2)
    .attr("cx", margin.left)

  const drag = d3.drag()
    .on("drag", function (event) {
      let newX = Math.max(margin.left, Math.min(width - margin.right, event.x))
      d3Handle.attr("cx", newX)
      const date = d3XScale.invert(newX)
      const index = d3.bisector(d => d).left(d3Dates, date)
      currentTimeIndex.value = Math.min(index, d3Dates.length - 1)
    })

  sliderGroup.call(drag)

  svg.on("click", function (event) {
    if (event.target.classList.contains('slider-handle')) return
    if (event.target.tagName === 'text') return 

    const coords = d3.pointer(event)
    let newX = Math.max(margin.left, Math.min(width - margin.right, coords[0]))
    d3Handle.transition().duration(200).attr("cx", newX)
    const date = d3XScale.invert(newX)
    const index = d3.bisector(d => d).left(d3Dates, date)
    currentTimeIndex.value = Math.min(index, d3Dates.length - 1)
  })
}

// --- Charts ---
function drawAllCharts() {
  if (troopsData.length === 0) return
  drawSingleChart('chart-french', 'french', '#3498db', charts.french)
  drawSingleChart('chart-russian', 'russian', '#2ecc71', charts.russian)
  drawSingleChart('chart-ratio', 'ratio', '#9b59b6', charts.ratio)
}

function drawSingleChart(containerId, dataKey, color, chartObj) {
  const container = document.getElementById(containerId)
  if (!container) return
  container.innerHTML = ""
  
  const width = container.clientWidth
  const height = 50 
  const margin = { top: 5, right: 5, bottom: 5, left: 5 }

  const svg = d3.select(container)
    .append("svg")
    .attr("width", width)
    .attr("height", height)

  const xScale = d3.scaleTime()
    .domain(d3.extent(troopsData, d => d.date))
    .range([margin.left, width - margin.right])

  const yScale = d3.scaleLinear()
    .domain([0, d3.max(troopsData, d => d[dataKey])])
    .range([height - margin.bottom, margin.top])

  const line = d3.line()
    .x(d => xScale(d.date))
    .y(d => yScale(d[dataKey]))
    .curve(d3.curveMonotoneX)

  svg.append("path")
    .datum(troopsData)
    .attr("fill", "none")
    .attr("stroke", color)
    .attr("stroke-width", 1.5)
    .attr("d", line)

  const area = d3.area()
    .x(d => xScale(d.date))
    .y0(height - margin.bottom)
    .y1(d => yScale(d[dataKey]))
    .curve(d3.curveMonotoneX)

  svg.append("path")
    .datum(troopsData)
    .attr("fill", color)
    .attr("fill-opacity", 0.1)
    .attr("d", area)

  const indicator = svg.append("g").style("display", "none")
  
  indicator.append("line")
    .attr("y1", 0)
    .attr("y2", height)
    .attr("stroke", "#666")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "2,2")

  indicator.append("circle")
    .attr("r", 3)
    .attr("fill", color)
    .attr("stroke", "#fff")
    .attr("stroke-width", 1)

  chartObj.svg = svg
  chartObj.indicator = indicator
  chartObj.xScale = xScale
  chartObj.yScale = yScale
}

function updateAllChartsIndicator(index) {
  if (!troopsData[index]) return
  const d = troopsData[index]
  updateSingleIndicator(charts.french, d.date, d.french, 'french-val', d.french.toLocaleString() + ' 人')
  updateSingleIndicator(charts.russian, d.date, d.russian, 'russian-val', d.russian.toLocaleString() + ' 人')
  updateSingleIndicator(charts.ratio, d.date, d.ratio, 'ratio-val', d.ratio + ' : 1')
}

function updateSingleIndicator(chartObj, date, value, domId, text) {
  if (chartObj.indicator && chartObj.xScale && chartObj.yScale) {
    const x = chartObj.xScale(date)
    const y = chartObj.yScale(value)
    chartObj.indicator.style("display", null)
    chartObj.indicator.attr("transform", `translate(${x}, 0)`)
    chartObj.indicator.select("circle").attr("cy", y)
  }
  const dom = document.getElementById(domId)
  if (dom) dom.innerText = text
}

function drawElevationChart(routePath) {
  const container = elevationChartRef.value
  if (!container) return

  container.innerHTML = ""
  const width = container.clientWidth
  const height = container.clientHeight
  const margin = { top: 10, right: 10, bottom: 20, left: 40 }

  const svg = d3.select(container)
    .append("svg")
    .attr("width", width)
    .attr("height", height)

  const data = routePath.map((p, i) => ({ idx: i, h: p[1] }))

  const x = d3.scaleLinear()
    .domain([0, data.length - 1])
    .range([margin.left, width - margin.right])

  const y = d3.scaleLinear()
    .domain([0, 1])
    .range([height - margin.bottom, margin.top])

  const defs = svg.append("defs")
  const gradient = defs.append("linearGradient")
    .attr("id", "area-gradient")
    .attr("x1", "0%").attr("y1", "0%")
    .attr("x2", "0%").attr("y2", "100%")

  gradient.append("stop").attr("offset", "0%").attr("stop-color", "#2980b9").attr("stop-opacity", 0.6)
  gradient.append("stop").attr("offset", "100%").attr("stop-color", "#aaccff").attr("stop-opacity", 0.1)

  const area = d3.area()
    .x(d => x(d.idx))
    .y0(height - margin.bottom)
    .y1(d => y(d.h))
    .curve(d3.curveMonotoneX)

  svg.append("path")
    .datum(data)
    .attr("fill", "url(#area-gradient)")
    .attr("d", area)

  const line = d3.line()
    .x(d => x(d.idx))
    .y(d => y(d.h))
    .curve(d3.curveMonotoneX)

  svg.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "#2980b9")
    .attr("stroke-width", 2)
    .attr("d", line)

  svg.append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(5).tickFormat(""))

  const yAxis = d3.axisLeft(y)
    .ticks(3)
    .tickFormat(d => Math.round(d * 1000) + "m")

  svg.append("g")
    .attr("transform", `translate(${margin.left}, 0)`)
    .call(yAxis)
    .attr("color", "#666")
    .style("font-size", "10px")
    .call(g => g.select(".domain").remove())

  svg.append("text")
    .attr("x", (width + margin.left) / 2)
    .attr("y", height - 5)
    .attr("text-anchor", "middle")
    .attr("font-size", "10px")
    .attr("fill", "#666")
    .text("地形起伏 (海拔剖面)")
}

function updateD3HandlePosition(index) {
  if (d3Dates[index] && d3Handle && d3XScale) {
    d3Handle.attr("cx", d3XScale(d3Dates[index]))
  }
}

// --- Three.js Logic ---

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
  
  renderer.outputEncoding = THREE.sRGBEncoding 
  renderer.toneMapping = THREE.ACESFilmicToneMapping 
  renderer.toneMappingExposure = 1.2

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

  const sun = new THREE.DirectionalLight(0xffffee, 1.8)
  sun.position.set(-50, 100, 50)
  sun.castShadow = true
  sun.shadow.mapSize.width = 2048
  sun.shadow.mapSize.height = 2048
  sun.shadow.camera.left = -150
  sun.shadow.camera.right = 150
  sun.shadow.camera.top = 150
  sun.shadow.camera.bottom = -150
  scene.add(sun)
  
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.9)
  scene.add(ambientLight)

  animate()
}

async function loadResources() {
  try {
    const texLoader = new THREE.TextureLoader()
    const [heightMap, textureMap, gameData] = await Promise.all([
      new Promise((resolve) => texLoader.load('/assets/heightmap.png', resolve)),
      new Promise((resolve) => texLoader.load('/assets/texture.png', resolve, undefined, () => resolve(null))),
      fetch('/game_data.json').then(r => r.json())
    ])

    loading.value = false
    
    if (textureMap) {
        textureMap.encoding = THREE.sRGBEncoding
    }

    if (gameData && gameData.timeline) {
      timelineData.value = gameData.timeline
      processTroopsData(gameData)
      setTimeout(() => {
          initD3Timeline(gameData)
          drawAllCharts()
          updateAllChartsIndicator(0)
          if (troopsData[0]) {
             currentEventName.value = troopsData[0].name || ''
          }
      }, 0)
    }

    buildWorld(heightMap, textureMap, gameData)
  } catch (e) {
    console.error('Failed to load resources:', e)
    loading.value = false
  }
}

function buildWorld(heightMap, textureMap, data) {
  const mat = new THREE.MeshStandardMaterial({
    color: textureMap ? 0xffffff : 0x5da668,
    map: textureMap || null,
    displacementMap: heightMap,
    displacementScale: CONFIG.heightScale,
    roughness: 0.8,
    metalness: 0.1
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
      opacity: 0.8,
      roughness: 0.2
    })
  )
  water.rotation.x = -Math.PI / 2
  water.position.y = CONFIG.waterLevel
  scene.add(water)

  setTimeout(() => drawVectors(data), 50)
}

function drawVectors(data) {
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
          isRoute: true,
          rawPath: route.path
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

function createRouteTube(points, color, radius) {
  if (points.length < 2) return null
  const vecs = points.map(p => new THREE.Vector3(
    p[0],
    Math.max(p[1] * CONFIG.heightScale, CONFIG.waterLevel) + 1.0,
    p[2]
  ))
  const curve = new THREE.CatmullRomCurve3(vecs)
  const geo = new THREE.TubeGeometry(curve, points.length * 2, radius, 8, false)
  const mat = new THREE.MeshStandardMaterial({ 
      color: color, 
      roughness: 0.4,
      emissive: color,
      emissiveIntensity: 0.2
  })
  const mesh = new THREE.Mesh(geo, mat)
  mesh.castShadow = true
  scene.add(mesh)
  return mesh
}

function drawLine(points, color) {
  const v = []
  points.forEach(p => {
    v.push(p[0], Math.max(p[1] * CONFIG.heightScale, CONFIG.waterLevel) + 0.2, p[2])
  })
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(v, 3))
  scene.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color: color, linewidth: 2 })))
}

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
    new THREE.MeshStandardMaterial({color: 0x888888})
  )
  mesh.position.y = 0.6 * scale
  mesh.castShadow = true
  grp.add(mesh)

  const div = document.createElement('div')
  
  let className = 'city-label'
  if (city.t === 'battle') className += ' battle-label'
  if (city.t === 'capital') className += ' capital-label'
  div.className = className

  div.textContent = city.n + (dateStr ? ` (${dateStr})` : "")
  div.style.opacity = '0'
  div.style.transition = 'opacity 0.3s'

  const label = new CSS2DObject(div)
  label.position.set(0, 3 * scale, 0)
  grp.add(label)

  createArrow(grp, color, label)
  scene.add(grp)
}

function createArrow(grp, color, labelObj) {
  const arrowMat = new THREE.MeshLambertMaterial({ 
      color: color, 
      emissive: 0x222222,
      emissiveIntensity: 0.5 
  })
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

// --- 修改部分：支持复选框筛选所有路线 ---
function updateRouteVisibility(idx) {
  routeMeshes.forEach(m => {
    const isAttack = m.userData.type === '进攻'
    const isRetreat = m.userData.type === '撤退'
    const isCurrent = m.userData.dateIdx === idx
    
    let visible = isCurrent // 默认：时间轴的当前帧始终可见

    // 筛选逻辑：如果勾选了"进攻"且该路线是进攻路线 -> 可见
    if (isAttack && showAllAttack.value) visible = true
    
    // 筛选逻辑：如果勾选了"撤退"且该路线是撤退路线 -> 可见
    if (isRetreat && showAllRetreat.value) visible = true

    m.visible = visible
  })
  if (selectedRoute && !selectedRoute.visible) {
    selectedRoute.material.emissive.setHex(0x000000)
    selectedRoute = null
  }
}

function unmapCoords(x, z) {
  const bounds = { min_lon: 20.0, max_lon: 45.0, min_lat: 50.0, max_lat: 60.0 }
  const nx = (x / CONFIG.worldWidth) + 0.5
  const lon = nx * (bounds.max_lon - bounds.min_lon) + bounds.min_lon
  const ny = -(z / CONFIG.worldHeight) + 0.5
  const lat = ny * (bounds.max_lat - bounds.min_lat) + bounds.min_lat
  return { lon, lat }
}

function onMouseClick(event) {
  if (event.target.closest('#timeline-container') || event.target.closest('.slider-handle')) return
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

function highlightRoute(mesh) {
  if (selectedRoute) {
    selectedRoute.material.emissive.setHex(selectedRoute.material.color.getHex())
    selectedRoute.material.emissiveIntensity = 0.2
  }
  selectedRoute = mesh
  selectedRoute.material.emissive.setHex(CONFIG.colors.highlight)
  selectedRoute.material.emissiveIntensity = 0.8
}

async function triggerAnalysis(mesh, point) {
  showAnalysisPanel.value = true
  if (mesh.userData.rawPath) {
    setTimeout(() => {
      drawElevationChart(mesh.userData.rawPath)
    }, 100)
  }
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
    const analysisText = result.analysis || "分析内容不可用"
    analysisContent.value = `
      <div style="font-size:12px; color:#999; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">
        📍 ${coords.lat.toFixed(2)}°N, ${coords.lon.toFixed(2)}°E <br>
        📅 ${dateStr} | 法军${mesh.userData.type}
      </div>
      <div class="analysis-text-content">
        ${analysisText.replace(/\n/g, '<br>')}
      </div>
    `
  } catch (e) {
    console.error('Analysis failed:', e)
    analysisContent.value = '<p style="color:red">分析服务连接失败，请确认后端服务已运行。</p>'
  }
}

function toggleViewMode() {
  is2DMode.value = !is2DMode.value
  const targetPos = is2DMode.value ? CONFIG.camera2D : CONFIG.camera3D
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
      if (is2DMode.value) {
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

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
  labelRenderer.setSize(window.innerWidth, window.innerHeight)
  if (timelineData.value.length > 0) {
    initD3Timeline({ timeline: timelineData.value })
    drawAllCharts()
    updateAllChartsIndicator(currentTimeIndex.value)
  }
}

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
/* === 核心修改：使用 fixed 定位铺满屏幕 === */
.napoleon-container {
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #aaccff;
  font-family: 'Segoe UI', sans-serif;
  
  /* 强制铺满全屏，脱离父容器流 */
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
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

/* === 紧凑版图例面板 === */
#ui-layer {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px;
  border-radius: 12px;
  pointer-events: none;
  z-index: 10;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  min-width: 160px;
}

/* 恢复鼠标交互以便点击 Checkbox */
.legend-section {
  pointer-events: auto; 
  margin-bottom: 10px;
}

/* 新增：让 Checkbox 所在行可以点击 */
.clickable {
    cursor: pointer;
}
.clickable label {
    cursor: pointer;
    display: flex;
    align-items: center;
}
.clickable input {
    margin-right: 6px;
    cursor: pointer;
}

#ui-layer h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.legend-title {
  font-size: 11px;
  font-weight: bold;
  color: #7f8c8d;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
  font-size: 13px;
  color: #333;
}

/* 新增/修改：图表区域样式 */
.chart-section {
    border-top: 1px solid #eee;
    padding-top: 8px;
    margin-top: 5px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2px;
  font-size: 11px;
}

.chart-label {
  font-weight: bold;
}

.chart-value {
  color: #333;
  font-family: monospace;
}

.mini-chart {
    width: 100%;
    height: 50px;
    margin-bottom: 8px;
    background: rgba(0,0,0,0.02);
    border-radius: 4px;
}

/* 图例图标样式 */
.icon {
  display: inline-block;
  margin-right: 8px;
  vertical-align: middle;
}
.line-attack { width: 18px; height: 3px; background: #d63031; border-radius: 2px; }
.line-retreat { width: 18px; height: 3px; background: #2d3436; border-radius: 2px; }

/* === 核心修改：将图例图标修改为倒三角（圆锥体投影） === */
.dot-capital {
  width: 14px;
  height: 18px; /* 比其他的高一点，突出首都 */
  background: #d63031;
  clip-path: polygon(0% 0%, 100% 0%, 50% 100%); /* 倒三角 */
}

.dot-battle {
  width: 12px;
  height: 15px;
  background: #f1c40f;
  clip-path: polygon(0% 0%, 100% 0%, 50% 100%); /* 倒三角 */
}

.dot-city {
  width: 10px;
  height: 12px;
  background: #95a5a6; /* 灰色 */
  clip-path: polygon(0% 0%, 100% 0%, 50% 100%); /* 倒三角 */
}
/* ================================================= */

.highlight-box { width: 10px; height: 10px; background: #ffff00; border: 1px solid #333; }

.tips {
  font-size: 11px;
  margin-top: 8px;
  color: #7f8c8d;
  font-style: italic;
  line-height: 1.4;
  border-top: 1px solid #eee;
  padding-top: 6px;
}

/* === 优化后的时间轴容器 === */
#timeline-container {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  height: 140px; /* 增加高度以容纳下方文字 */
  background: rgba(255, 255, 255, 0.95);
  padding: 5px 20px;
  border-radius: 15px;
  z-index: 10;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

#date-display {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 2px;
  font-family: 'Times New Roman', serif;
  text-align: center;
}

/* 新增：当前事件名称样式 */
.event-name {
  font-size: 14px;
  color: #666;
  font-weight: normal;
  margin-top: 4px;
  font-family: 'Segoe UI', sans-serif;
  height: 20px; /* 预留高度防止跳动 */
}

#d3-timeline {
  width: 100%;
  flex: 1;
  position: relative;
  min-height: 0;
  cursor: pointer;
}

/* D3 样式 */
:deep(.axis path), :deep(.axis line) { stroke: #888; }
:deep(.axis text) { font-family: 'Segoe UI', sans-serif; font-size: 10px; color: #666; }
:deep(.slider-handle) { fill: #fff; stroke: #2c3e50; stroke-width: 2px; filter: drop-shadow(0 2px 2px rgba(0, 0, 0, 0.3)); cursor: grab; }
:deep(.slider-handle:active) { cursor: grabbing; }

#view-btn {
  position: absolute; top: 20px; right: 20px;
  padding: 10px 20px; background: #2c3e50; color: white;
  border: none; border-radius: 5px; cursor: pointer;
  z-index: 100; font-weight: bold;
}
#view-btn:hover { background: #34495e; }

/* === 紧凑版分析面板 === */
#analysis-panel {
  position: absolute;
  top: 80px;
  right: -350px;
  width: 300px;
  max-height: 80vh;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 16px;
  box-shadow: -5px 5px 20px rgba(0, 0, 0, 0.2);
  transition: right 0.4s ease;
  z-index: 100;
}
#analysis-panel.active { right: 20px; }

.panel-header {
  display: flex; justify-content: space-between; border-bottom: 1px solid #ddd;
  padding-bottom: 8px; margin-bottom: 10px;
}
.close-btn { cursor: pointer; border: none; background: none; font-size: 18px; }

#d3-elevation-chart {
  width: 100%;
  height: 120px;
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

/* 分析文本内容样式 */
:deep(.analysis-text-content) {
  font-family: 'Times New Roman', serif;
  line-height: 1.5;
  color: #2c3e50;
  text-align: justify;
  font-size: 14px;
}

/* 标签样式 */
:deep(.city-label) { color: white; background: rgba(0, 0, 0, 0.6); padding: 4px 8px; border-radius: 4px; font-size: 12px; pointer-events: none; margin-top: -5px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3); }
:deep(.battle-label) { border: 1px solid #f1c40f; color: #f1c40f; background: rgba(0, 0, 0, 0.85); font-weight: bold; padding: 5px 10px; font-size: 13px; }
:deep(.capital-label) { background: rgba(192, 57, 43, 0.9); font-weight: bold; font-size: 14px; border: 1px solid white; }

.loading-text { text-align: center; color: #666; padding: 20px; }
</style>