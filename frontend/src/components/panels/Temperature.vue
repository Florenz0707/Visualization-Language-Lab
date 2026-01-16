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
      <div class="current-time-display">
        <span class="time-label">当前时间:</span>
        <span class="time-value">{{ formatDate(mapStore.currentTime) }}</span>
      </div>
      <div class="current-temp">
        <span class="temp-label">当前平均气温:</span>
        <span class="temp-value">{{ currentTemperature }} °C</span>
      </div>
      <div ref="chartContainer" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useMapStore } from '@/stores/map'
import * as d3 from 'd3'

// 状态管理
const mapStore = useMapStore()
const loading = ref(false)
const error = ref(null)
const isCollapsed = ref(false)
const temperatureData = ref([])
const chartContainer = ref(null)
let svg = null
let xScale = null
let yScale = null
let lineGenerator = null
let chartDimensions = { width: 600, height: 300, margin: { top: 20, right: 20, bottom: 40, left: 50 } }

// 折叠切换
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  // 折叠/展开时重绘图表
  if (!isCollapsed.value && temperatureData.value.length > 0) {
    drawChart()
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

// 生成模拟气温数据（实际项目中替换为API请求）
const generateTemperatureData = (startDate, endDate) => {
  const start = new Date(startDate)
  const end = new Date(endDate)
  const data = []
  
  // 1812年拿破仑远征期间的气温特征：6-9月温暖，10-12月急剧下降
  const baseTemps = {
    6: 18, 7: 22, 8: 20, 9: 12, 10: 5, 11: -5, 12: -15
  }

  let currentDate = new Date(start)
  while (currentDate <= end) {
    const month = currentDate.getMonth() + 1 // 月份从1开始
    const baseTemp = baseTemps[month] || 0
    // 添加随机波动
    const temp = baseTemp + (Math.random() * 4 - 2)
    data.push({
      date: new Date(currentDate),
      temperature: parseFloat(temp.toFixed(1))
    })
    // 按天生成数据
    currentDate.setDate(currentDate.getDate() + 1)
  }
  return data
}

// 加载气温数据
const loadTemperatureData = async () => {
  loading.value = true
  error.value = null

  try {
    // 模拟API请求（实际项目中替换为真实接口）
    await new Promise(resolve => setTimeout(resolve, 800))
    
    // 基于地图时间范围生成数据
    const data = generateTemperatureData(
      mapStore.timeRange.start,
      mapStore.timeRange.end
    )
    temperatureData.value = data
    drawChart()
  } catch (err) {
    error.value = '加载气温数据失败'
    console.error('Error loading temperature data:', err)
  } finally {
    loading.value = false
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

  // 创建SVG
  svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', chartDimensions.width)
    .attr('height', chartDimensions.height)
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
    .text('气温 (°C)')

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

  // 更新X轴
  svg.select('.x-axis')
    .call(d3.axisBottom(xScale).ticks(6).tickFormat(d3.timeFormat('%Y-%m-%d')))
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

// 监听地图时间变化，更新当前气温和图表标记
watch(() => mapStore.currentTime, () => {
  if (temperatureData.value.length > 0 && !isCollapsed.value) {
    drawChart()
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

.current-time-display, .current-temp {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.time-label, .temp-label {
  font-size: 12px;
  color: #64748b;
  margin-right: 8px;
}

.time-value, .temp-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.chart-container {
  width: 100%;
  height: 300px;
  min-height: 300px;
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