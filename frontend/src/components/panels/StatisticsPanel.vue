<template>
  <div class="statistics-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-header">
      <h3 class="title">兵力统计</h3>
      <div class="header-actions">
        <div class="status-badge" v-if="!isCollapsed">
          <span v-if="loading">加载中...</span>
          <span v-else-if="error">错误</span>
          <span v-else>{{ totalDataPoints }} 个数据点</span>
        </div>
        <button @click="toggleCollapse" class="collapse-btn" :title="isCollapsed ? '展开' : '折叠'">
          {{ isCollapsed ? '▶' : '◀' }}
        </button>
      </div>
    </div>

    <div v-if="!isCollapsed && loading" class="loading">
      <div class="spinner"></div>
      <span>正在加载统计数据...</span>
    </div>

    <div v-else-if="!isCollapsed && error" class="error">
      <span>⚠️ {{ error }}</span>
      <button @click="loadStatistics" class="retry-btn">重试</button>
    </div>

    <div v-else-if="!isCollapsed && totalDataPoints === 0" class="empty">
      <span>暂无统计数据</span>
      <button @click="loadStatistics" class="retry-btn">刷新</button>
    </div>

    <div v-else-if="!isCollapsed" class="statistics-content">
      <div class="stats-summary">
        <div class="stat-item french">
          <div class="stat-label">法军</div>
          <div class="stat-value">{{ currentFrenchCount }}</div>
          <div class="stat-date">{{ currentFrenchDate }}</div>
        </div>
        <div class="stat-item russian">
          <div class="stat-label">俄军</div>
          <div class="stat-value">{{ currentRussianCount }}</div>
          <div class="stat-date">{{ currentRussianDate }}</div>
        </div>
      </div>

      <!-- 新增：兵力对比饼状图容器 -->
      <div class="chart-container" v-if="currentFrenchCount !== '-' && currentRussianCount !== '-'">
        <h4 class="chart-title">兵力占比对比</h4>
        <div id="troop-pie-chart"></div>
      </div>

      <div class="current-time-display">
        <span class="time-label">当前时间:</span>
        <span class="time-value">{{ formatDate(mapStore.currentTime) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useMapStore } from '@/stores/map'
import { fetchTroopStatistics } from '@/services/api'
import * as d3 from 'd3'

const mapStore = useMapStore()
const loading = ref(false)
const error = ref(null)
const statisticsData = ref({ french: [], russian: [] })
const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const totalDataPoints = computed(() => {
  const frenchCount = statisticsData.value.french?.length || 0
  const russianCount = statisticsData.value.russian?.length || 0
  return frenchCount + russianCount
})

// 根据当前时间使用线性插值计算兵力
const interpolateDataAtTime = (data, currentTime) => {
  if (!data || data.length === 0) return null

  const currentTimestamp = currentTime.getTime()

  // 找到当前时间所在的区间
  let beforeData = null
  let afterData = null

  for (let i = 0; i < data.length; i++) {
    const dataTime = new Date(data[i].date).getTime()

    if (dataTime <= currentTimestamp) {
      beforeData = data[i]
    } else {
      afterData = data[i]
      break
    }
  }

  // 如果当前时间在第一个数据点之前,返回null
  if (!beforeData) return null

  // 如果当前时间在最后一个数据点之后,返回最后一个数据点
  if (!afterData) return beforeData

  // 线性插值计算
  const beforeTime = new Date(beforeData.date).getTime()
  const afterTime = new Date(afterData.date).getTime()
  const beforeCount = beforeData.count
  const afterCount = afterData.count

  // 计算时间比例
  const timeRatio = (currentTimestamp - beforeTime) / (afterTime - beforeTime)

  // 线性插值计算兵力
  const interpolatedCount = Math.round(beforeCount + (afterCount - beforeCount) * timeRatio)

  return {
    count: interpolatedCount,
    date: currentTime,
    isInterpolated: true,
    fromDate: beforeData.date,
    toDate: afterData.date
  }
}

const currentFrenchData = computed(() => {
  return interpolateDataAtTime(statisticsData.value.french, mapStore.currentTime)
})

const currentRussianData = computed(() => {
  return interpolateDataAtTime(statisticsData.value.russian, mapStore.currentTime)
})

const currentFrenchCount = computed(() => {
  return currentFrenchData.value ? currentFrenchData.value.count.toLocaleString() : '-'
})

const currentRussianCount = computed(() => {
  return currentRussianData.value ? currentRussianData.value.count.toLocaleString() : '-'
})

const currentFrenchDate = computed(() => {
  if (!currentFrenchData.value) return '无数据'
  if (currentFrenchData.value.isInterpolated) {
    return '插值计算'
  }
  return formatDate(currentFrenchData.value.date)
})

const currentRussianDate = computed(() => {
  if (!currentRussianData.value) return '无数据'
  if (currentRussianData.value.isInterpolated) {
    return '插值计算'
  }
  return formatDate(currentRussianData.value.date)
})

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 初始化/更新饼状图
const updatePieChart = () => {
  // 确保有有效数据
  if (currentFrenchData.value?.count === undefined || currentRussianData.value?.count === undefined) {
    return
  }

  const frenchCount = currentFrenchData.value.count
  const russianCount = currentRussianData.value.count
  const total = frenchCount + russianCount

  // 移除旧图表
  d3.select('#troop-pie-chart').selectAll('*').remove()

  // 图表尺寸
  const width = 360
  const height = 220
  const radius = Math.min(width, height) / 2.5

  // 创建SVG容器
  const svg = d3.select('#troop-pie-chart')
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .append('g')
    .attr('transform', `translate(${width / 2}, ${height / 2})`)

  // 定义颜色
  const color = d3.scaleOrdinal()
    .domain(['法军', '俄军'])
    .range(['#3b82f6', '#ef4444'])

  // 准备数据
  const data = [
    { name: '法军', value: frenchCount },
    { name: '俄军', value: russianCount }
  ]

  // 创建饼图生成器
  const pie = d3.pie()
    .value(d => d.value)
    .sort(null)

  // 创建弧生成器
  const arc = d3.arc()
    .innerRadius(radius * 0.4) // 内环半径（甜甜圈效果）
    .outerRadius(radius)

  // 创建外部标签弧生成器
  const labelArc = d3.arc()
    .innerRadius(radius * 1.1)
    .outerRadius(radius * 1.1)

  // 绘制饼图路径
  const paths = svg.selectAll('path')
    .data(pie(data))
    .enter()
    .append('path')
    .attr('d', arc)
    .attr('fill', d => color(d.data.name))
    .attr('stroke', 'white')
    .style('stroke-width', '2px')
    .style('opacity', 0.8)
    // 添加鼠标悬浮效果
    .on('mouseover', function() {
      d3.select(this).style('opacity', 1)
    })
    .on('mouseout', function() {
      d3.select(this).style('opacity', 0.8)
    })

  // 添加百分比标签
  svg.selectAll('text')
    .data(pie(data))
    .enter()
    .append('text')
    .attr('transform', d => `translate(${labelArc.centroid(d)})`)
    .attr('dy', '.35em')
    .style('text-anchor', 'middle')
    .style('font-size', '12px')
    .style('font-weight', '600')
    .text(d => {
      const percent = ((d.value / total) * 100).toFixed(1)
      return `${d.data.name} ${percent}%`
    })

  // 添加中心文本
  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '0em')
    .style('font-size', '14px')
    .style('font-weight', '700')
    .style('color', '#1e293b')
    .text(`总计 ${total.toLocaleString()}`)
  
  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.5em')
    .style('font-size', '12px')
    .style('color', '#64748b')
    .text('兵力总数')
}

const loadStatistics = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('Loading statistics...')
    const data = await fetchTroopStatistics({
      start: mapStore.timeRangeString.start,
      end: mapStore.timeRangeString.end,
      period: 'month'
    })

    console.log('Statistics API response:', data)
    statisticsData.value = data
    
    // 数据加载完成后更新饼图
    nextTick(() => {
      updatePieChart()
    })
  } catch (err) {
    error.value = '加载统计数据失败'
    console.error('Error loading statistics:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  console.log('StatisticsPanel mounted')
  loadStatistics()
})

// 监听时间变化更新饼图
watch([currentFrenchData, currentRussianData], () => {
  if (!isCollapsed.value && currentFrenchCount.value !== '-' && currentRussianCount.value !== '-') {
    nextTick(() => {
      updatePieChart()
    })
  }
}, { deep: true })

// 监听折叠状态变化更新饼图
watch(isCollapsed, (newVal) => {
  if (!newVal && currentFrenchCount.value !== '-' && currentRussianCount.value !== '-') {
    nextTick(() => {
      updatePieChart()
    })
  }
})

watch(() => mapStore.timeRange, () => {
  loadStatistics()
}, { deep: true })
</script>

<style scoped>
.statistics-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  transition: all 0.3s ease;
}

.statistics-panel.collapsed {
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

.statistics-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.stat-item.french {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #93c5fd;
}

.stat-item.russian {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border: 1px solid #fca5a5;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 600;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.stat-date {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}

/* 新增：饼图容器样式 */
.chart-container {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  margin: 8px 0;
}

.chart-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  text-align: center;
}

#troop-pie-chart {
  display: flex;
  justify-content: center;
  align-items: center;
}

.current-time-display {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.time-label {
  font-size: 12px;
  color: #64748b;
  margin-right: 8px;
}

.time-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}
</style>