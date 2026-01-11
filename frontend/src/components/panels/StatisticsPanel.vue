<template>
  <div class="statistics-panel">
    <div class="panel-header">
      <h3 class="title">📊 兵力统计</h3>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="error">
      <span>⚠️ {{ error }}</span>
    </div>

    <div v-else class="charts-container">
      <div ref="chartContainer" class="chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as d3 from 'd3'
import { useMapStore } from '@/stores/map'
import { fetchTroopStatistics } from '@/services/api'

const mapStore = useMapStore()
const chartContainer = ref(null)
const loading = ref(false)
const error = ref(null)
const statisticsData = ref(null)

const loadStatistics = async () => {
  loading.value = true
  error.value = null

  try {
    const data = await fetchTroopStatistics({
      start: mapStore.timeRangeString.start,
      end: mapStore.timeRangeString.end,
      period: 'month'
    })

    statisticsData.value = data
    renderChart()
  } catch (err) {
    error.value = '加载统计数据失败'
    console.error('Error loading statistics:', err)
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartContainer.value || !statisticsData.value) return

  // Clear previous chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 20, right: 20, bottom: 40, left: 60 }
  const width = 400 - margin.left - margin.right
  const height = 250 - margin.top - margin.bottom

  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Prepare data
  const french = statisticsData.value.french || []
  const russian = statisticsData.value.russian || []

  if (french.length === 0 && russian.length === 0) return

  // X scale
  const allDates = [...french, ...russian].map(d => new Date(d.date))
  const x = d3.scaleTime()
    .domain(d3.extent(allDates))
    .range([0, width])

  // Y scale
  const maxCount = d3.max([...french, ...russian], d => d.count) || 0
  const y = d3.scaleLinear()
    .domain([0, maxCount])
    .range([height, 0])

  // Line generator
  const line = d3.line()
    .x(d => x(new Date(d.date)))
    .y(d => y(d.count))

  // Draw French line
  if (french.length > 0) {
    svg.append('path')
      .datum(french)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2)
      .attr('d', line)
  }

  // Draw Russian line
  if (russian.length > 0) {
    svg.append('path')
      .datum(russian)
      .attr('fill', 'none')
      .attr('stroke', '#ef4444')
      .attr('stroke-width', 2)
      .attr('d', line)
  }

  // X axis
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(5))

  // Y axis
  svg.append('g')
    .call(d3.axisLeft(y).ticks(5))

  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(${width - 100}, 10)`)

  legend.append('line')
    .attr('x1', 0)
    .attr('x2', 20)
    .attr('y1', 0)
    .attr('y2', 0)
    .attr('stroke', '#3b82f6')
    .attr('stroke-width', 2)

  legend.append('text')
    .attr('x', 25)
    .attr('y', 4)
    .text('法军')
    .style('font-size', '12px')

  legend.append('line')
    .attr('x1', 0)
    .attr('x2', 20)
    .attr('y1', 20)
    .attr('y2', 20)
    .attr('stroke', '#ef4444')
    .attr('stroke-width', 2)

  legend.append('text')
    .attr('x', 25)
    .attr('y', 24)
    .text('俄军')
    .style('font-size', '12px')
}

onMounted(() => {
  loadStatistics()
})

watch(() => mapStore.timeRange, () => {
  loadStatistics()
}, { deep: true })
</script>

<style scoped>
.statistics-panel {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  backdrop-filter: blur(10px);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.panel-header {
  margin-bottom: 16px;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
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
}

.charts-container {
  overflow-x: auto;
  background: white;
  padding: 16px;
  border-radius: 12px;
}

.chart {
  min-height: 250px;
}
</style>
