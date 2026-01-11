<template>
  <div class="arc-diagram-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-header">
      <h3 class="title">事件序列</h3>
      <div class="header-actions">
        <div class="status-badge" v-if="!isCollapsed">
          <span v-if="loading">加载中...</span>
          <span v-else-if="error">错误</span>
          <span v-else>{{ events.length }} 个事件</span>
        </div>
        <button @click="toggleCollapse" class="collapse-btn" :title="isCollapsed ? '展开' : '折叠'">
          {{ isCollapsed ? '▶' : '◀' }}
        </button>
      </div>
    </div>

    <div v-if="!isCollapsed && loading" class="loading">
      <div class="spinner"></div>
      <span>正在加载事件数据...</span>
    </div>

    <div v-else-if="!isCollapsed && error" class="error">
      <span>⚠️ {{ error }}</span>
      <button @click="loadEvents" class="retry-btn">重试</button>
    </div>

    <div v-else-if="!isCollapsed && events.length === 0" class="empty">
      <span>暂无事件数据</span>
      <button @click="loadEvents" class="retry-btn">刷新</button>
    </div>

    <div v-else-if="!isCollapsed" class="events-list">
      <div
        v-for="event in events"
        :key="event.id"
        class="event-item"
        @click="handleEventClick(event)"
      >
        <div class="event-marker" :style="{ backgroundColor: getEventColor(event.type) }"></div>
        <div class="event-content">
          <div class="event-name">{{ event.name }}</div>
          <div class="event-date">{{ formatDate(event.date) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMapStore } from '@/stores/map'
import { fetchEvents } from '@/services/api'

const mapStore = useMapStore()
const loading = ref(false)
const error = ref(null)
const events = ref([])
const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const eventColors = {
  battle: '#dc2626',
  movement: '#3b82f6',
  occupation: '#16a34a',
  retreat: '#ef4444',
  city: '#2563eb',
  camp: '#16a34a'
}

const getEventColor = (type) => {
  return eventColors[type] || '#6b7280'
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const handleEventClick = (event) => {
  console.log('Event clicked:', event)
  mapStore.setCurrentTime(event.date)
}

const loadEvents = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('Loading events...')
    const data = await fetchEvents({
      projection: mapStore.projection
    })

    console.log('Events API response:', data)

    // Extract and sort events by date
    events.value = data.features
      .filter(f => f.properties.date)
      .map(f => ({
        id: f.properties.id || f.properties.name,
        name: f.properties.name,
        date: new Date(f.properties.date),
        type: f.properties.type
      }))
      .sort((a, b) => a.date - b.date)

    console.log('Processed events:', events.value.length)
  } catch (err) {
    error.value = '加载事件数据失败'
    console.error('Error loading events:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  console.log('ArcDiagram mounted')
  loadEvents()
})
</script>

<style scoped>
.arc-diagram-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  transition: all 0.3s ease;
}

.arc-diagram-panel.collapsed {
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

.events-list {
  display: flex;
  flex-direction: column;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
}

.event-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateX(4px);
}

.event-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-content {
  flex: 1;
  min-width: 0;
}

.event-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-date {
  font-size: 12px;
  color: #64748b;
}
</style>
