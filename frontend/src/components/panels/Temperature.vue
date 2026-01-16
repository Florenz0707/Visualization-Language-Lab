<template>
  <div class="temperature-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-header">
      <h3 class="title">气温变化</h3>
      <div class="header-actions">
        <div class="status-badge" v-if="!isCollapsed">
          <span v-if="loading">加载中...</span>
          <span v-else-if="error">错误</span>
          <span v-else>{{ temperatureData.length }} 个气温数据点</span>
        </div>
        <button @click="toggleCollapse" class="collapse-btn" :title="isCollapsed ? '展开' : '折叠'">
          {{ isCollapsed ? '▶' : '◀' }}
        </button>
      </div>
    </div>

    <div v-if="!isCollapsed && loading" class="loading">
      <div class="spinner"></div>
      <span>正在加载气温数据...</span>
    </div>

    <div v-else-if="!isCollapsed && error" class="error">
      <span>⚠️ {{ error }}</span>
      <button @click="loadTemperatureData" class="retry-btn">重试</button>
    </div>

    <div v-else-if="!isCollapsed && temperatureData.length === 0" class="empty">
      <span>暂无气温数据</span>
      <button @click="loadTemperatureData" class="retry-btn">刷新</button>
    </div>

    <div v-else-if="!isCollapsed" class="temperature-content">
      <div class="current-temp">
        <span class="temp-label">当前平均气温:</span>
        <span class="temp-value">{{ currentTemperature }} °C</span>
      </div>
      <div ref="chartContainer" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useMapStore } from '@/stores/map'
import { fetchTemperature } from '@/services/api'
import * as d3 from 'd3'

// 状态管理
const mapStore = useMapStore()
const loading = ref(false)
const error = ref(null)
const isCollapsed = ref(false)
const temperatureData = ref([])
const chartContainer = ref(null)
let svgContainer = null  // SVG容器
let svg = null  // g元素（绘图区域）
let xScale = null
let yScale = null
let lineGenerator = null
let chartDimensions = { width: 450, height: 300, margin: { top: 20, right: 5, bottom: 30, left: 20 } }

// 折叠切换
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  // 折叠/展开时重绘图表
  if (!isCollapsed.value && temperatureData.value.length > 0) {
    // 使用nextTick等待DOM更新后再绘制
    nextTick(() => {
      // 清空SVG引用，强制重新初始化
      svg = null
      svgContainer = null
      drawChart()
    })
  }
}

// 格式化日期
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 从CSV加载真实的温度数据并进行线性插值
const loadTemperatureData = async () => {
  loading.value = true
  error.value = null

  try {
    // 加载CSV文件
    const response = await fetch('/data/temperature_1812.csv')
    const csvText = await response.text()

    // 解析CSV
    const lines = csvText.trim().split('\n')
    const headers = lines[0].split(',')

    // 提取温度数据点
    const rawDataPoints = []
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',')
      if (values.length >= 2) {
        const date = new Date(values[0].trim())
        const temp = parseFloat(values[1].trim()) // tavg_abs 列
        if (!isNaN(temp) && date instanceof Date && !isNaN(date)) {
          rawDataPoints.push({ date, temperature: temp })
        }
      }
    }

    // 按日期排序
    rawDataPoints.sort((a, b) => a.date - b.date)

    // 使用线性插值生成每日数据
    const start = new Date(mapStore.timeRange.start)
    const end = new Date(mapStore.timeRange.end)
    const interpolatedData = []

    let currentDate = new Date(start)
    const dayInMs = 24 * 60 * 60 * 1000

    while (currentDate <= end) {
      const currentTime = currentDate.getTime()

      // 找到当前日期前后的数据点
      let beforePoint = null
      let afterPoint = null

      for (let i = 0; i < rawDataPoints.length; i++) {
        const pointTime = rawDataPoints[i].date.getTime()
        if (pointTime <= currentTime) {
          beforePoint = rawDataPoints[i]
        } else {
          afterPoint = rawDataPoints[i]
          break
        }
      }

      let temperature
      if (!beforePoint) {
        // 当前日期在第一个数据点之前，使用第一个数据点的温度
        temperature = rawDataPoints[0].temperature
      } else if (!afterPoint) {
        // 当前日期在最后一个数据点之后，使用最后一个数据点的温度
        temperature = beforePoint.temperature
      } else {
        // 线性插值
        const beforeTime = beforePoint.date.getTime()
        const afterTime = afterPoint.date.getTime()
        const ratio = (currentTime - beforeTime) / (afterTime - beforeTime)
        temperature = beforePoint.temperature + (afterPoint.temperature - beforePoint.temperature) * ratio
      }

      interpolatedData.push({
        date: new Date(currentDate),
        temperature: parseFloat(temperature.toFixed(1))
      })

      currentDate = new Date(currentDate.getTime() + dayInMs)
    }

    temperatureData.value = interpolatedData

    // 不在这里调用 drawChart，等待 loading 状态改变后 DOM 更新
  } catch (err) {
    error.value = '加载气温数据失败'
    console.error('Error loading temperature data:', err)
  } finally {
    loading.value = false
    // loading 状态改变后，使用 nextTick 等待 DOM 更新，然后绘制图表
    nextTick(() => {
      if (temperatureData.value.length > 0 && !isCollapsed.value) {
        drawChart()
      }
    })
  }
}

// 线性插值计算当前气温
const interpolateTemperature = (data, currentTime) => {
  if (!data || data.length === 0) return '—'

  const currentTimestamp = currentTime.getTime()
  let beforeData = null
  let afterData = null

  // 找到当前时间所在的区间
  for (let i = 0; i < data.length; i++) {
    const dataTime = data[i].date.getTime()
    if (dataTime <= currentTimestamp) {
      beforeData = data[i]
    } else {
      afterData = data[i]
      break
    }
  }

  // 边界情况处理
  if (!beforeData) return '—'
  if (!afterData) return beforeData.temperature.toFixed(1)

  // 线性插值计算
  const beforeTime = beforeData.date.getTime()
  const afterTime = afterData.date.getTime()
  const beforeTemp = beforeData.temperature
  const afterTemp = afterData.temperature

  const timeRatio = (currentTimestamp - beforeTime) / (afterTime - beforeTime)
  const interpolatedTemp = beforeTemp + (afterTemp - beforeTemp) * timeRatio

  return interpolatedTemp.toFixed(1)
}

// 计算当前气温
const currentTemperature = computed(() => {
  return interpolateTemperature(temperatureData.value, mapStore.currentTime)
})

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return

  // 清空容器
  d3.select(chartContainer.value).selectAll('*').remove()

  // 创建SVG容器
  svgContainer = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', chartDimensions.width)
    .attr('height', chartDimensions.height)

  // 创建g元素（绘图区域）
  svg = svgContainer
    .append('g')
    .attr('transform', `translate(${chartDimensions.margin.left}, ${chartDimensions.margin.top})`)

  // 定义比例尺
  const innerWidth = chartDimensions.width - chartDimensions.margin.left - chartDimensions.margin.right
  const innerHeight = chartDimensions.height - chartDimensions.margin.top - chartDimensions.margin.bottom

  // X轴：时间比例尺
  xScale = d3.scaleTime()
    .range([0, innerWidth])

  // Y轴：线性比例尺（气温范围-20到25℃）
  yScale = d3.scaleLinear()
    .domain([-20, 25])
    .range([innerHeight, 0])

  // 创建X轴
  svg.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0, ${innerHeight})`)

  // 创建Y轴
  svg.append('g')
    .attr('class', 'y-axis')

  // 添加Y轴标签
  svg.append('text')
    .attr('class', 'y-label')
    .attr('transform', 'rotate(-90)')
    .attr('y', -chartDimensions.margin.left + 10)
    .attr('x', -innerHeight / 2)
    .attr('text-anchor', 'middle')

  // 定义折线生成器
  lineGenerator = d3.line()
    .x(d => xScale(d.date))
    .y(d => yScale(d.temperature))
    .curve(d3.curveMonotoneX) // 平滑曲线
}

// 绘制图表
const drawChart = () => {
  if (!chartContainer.value || temperatureData.value.length === 0 || isCollapsed.value) return

  if (!svg) {
    initChart()
  }

  const innerWidth = chartDimensions.width - chartDimensions.margin.left - chartDimensions.margin.right
  const innerHeight = chartDimensions.height - chartDimensions.margin.top - chartDimensions.margin.bottom

  // 更新X轴定义域
  xScale.domain([
    new Date(mapStore.timeRange.start),
    new Date(mapStore.timeRange.end)
  ])

  // 生成每月1日和15日的刻度值
  const start = new Date(mapStore.timeRange.start)
  const end = new Date(mapStore.timeRange.end)
  const tickValues = []

  let currentDate = new Date(start.getFullYear(), start.getMonth(), 1)
  while (currentDate <= end) {
    if (currentDate >= start) {
      tickValues.push(new Date(currentDate))
      // 添加15日
      const fifteenth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 15)
      if (fifteenth <= end) {
        tickValues.push(fifteenth)
      }
    }
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
  }

  // 更新X轴
  svg.select('.x-axis')
    .call(d3.axisBottom(xScale)
      .tickValues(tickValues)
      .tickFormat(d3.timeFormat('%m-%d')))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')

  // 更新Y轴
  svg.select('.y-axis')
    .call(d3.axisLeft(yScale).ticks(10))

  // 移除旧折线
  svg.selectAll('.temp-line').remove()
  svg.selectAll('.temp-area').remove()
  svg.selectAll('.current-time-marker').remove()

  // 添加面积填充
  svg.append('path')
    .attr('class', 'temp-area')
    .datum(temperatureData.value)
    .attr('fill', 'rgba(59, 130, 246, 0.2)')
    .attr('d', d3.area()
      .x(d => xScale(d.date))
      .y0(yScale(0))
      .y1(d => yScale(d.temperature))
      .curve(d3.curveMonotoneX)
    )

  // 添加温度折线
  svg.append('path')
    .attr('class', 'temp-line')
    .datum(temperatureData.value)
    .attr('fill', 'none')
    .attr('stroke', '#3b82f6')
    .attr('stroke-width', 2)
    .attr('d', lineGenerator)

  // 添加当前时间标记线
  const currentTimeX = xScale(mapStore.currentTime)
  svg.append('line')
    .attr('class', 'current-time-marker')
    .attr('x1', currentTimeX)
    .attr('y1', 0)
    .attr('x2', currentTimeX)
    .attr('y2', innerHeight)
    .attr('stroke', '#ef4444')
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '5,5')
}

// 只更新时间标记线（性能优化 - 使用D3 transition）
const updateTimeMarker = () => {
  if (!svg || !xScale || isCollapsed.value) return

  const innerHeight = chartDimensions.height - chartDimensions.margin.top - chartDimensions.margin.bottom
  const currentTimeX = xScale(mapStore.currentTime)

  // 查找现有标记线
  let marker = svg.select('.current-time-marker')

  if (marker.empty()) {
    // 如果不存在，创建新的
    marker = svg.append('line')
      .attr('class', 'current-time-marker')
      .attr('y1', 0)
      .attr('y2', innerHeight)
      .attr('stroke', '#ef4444')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '5,5')
  }

  // 使用transition平滑更新位置
  marker
    .attr('x1', currentTimeX)
    .attr('x2', currentTimeX)
}

// 使用requestAnimationFrame进行更高效的更新
let rafId = null
const throttledUpdateTimeMarker = () => {
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    updateTimeMarker()
    rafId = null
  })
}

// 监听地图时间变化，只更新时间标记
watch(() => mapStore.currentTime, () => {
  if (temperatureData.value.length > 0 && !isCollapsed.value && svg) {
    throttledUpdateTimeMarker()
  }
})

// 监听时间范围变化，重新加载数据
watch(() => mapStore.timeRange, () => {
  loadTemperatureData()
}, { deep: true })

// 组件挂载时初始化
onMounted(() => {
  loadTemperatureData()
  // 监听窗口大小变化，自适应图表
  window.addEventListener('resize', drawChart)
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', drawChart)
})
</script>

<style scoped>
.temperature-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  transition: all 0.3s ease;
}

.temperature-panel.collapsed {
  width: auto;
  padding: 20px;
}

.panel-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.status-badge {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 12px;
  border-radius: 12px;
}

.collapse-btn {
  padding: 6px 10px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: #e2e8f0;
  color: #475569;
}

.loading {
  padding: 40px 20px;
  text-align: center;
  color: #64748b;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  padding: 20px;
  text-align: center;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
  border-radius: 8px;
  font-weight: 500;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.empty {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.retry-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
}

.temperature-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.current-temp {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.temp-label {
  font-size: 12px;
  color: #64748b;
  margin-right: 8px;
}

.temp-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.chart-container {
  align-items: center;
  width: 100%;
  height: 300px;
  min-height: 100px;
}

/* D3图表样式 */
.x-axis, .y-axis {
  font-size: 12px;
  color: #64748b;
}

.y-label {
  font-size: 12px;
  color: #64748b;
}

.temp-line {
  stroke-linecap: round;
  stroke-linejoin: round;
}

.current-time-marker {
  z-index: 10;
}
</style>
