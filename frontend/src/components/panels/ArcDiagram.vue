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

    <!-- 事件列表 + 详情区域 -->
    <div v-else-if="!isCollapsed" class="events-container">
      <div class="events-list">
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

      <!-- 事件详情：图片 + 音频 + 退出按钮 -->
      <div v-if="currentEvent" class="event-detail">
        <!-- 新增：详情头部（标题+退出按钮） -->
        <div class="event-detail-header">
          <h4 class="event-detail-title">{{ currentEvent.title }}</h4>
          <button @click="exitEventDetail" class="exit-btn">退出</button>
        </div>

        <div class="event-image-wrapper">
          <img
            v-if="currentEvent.imageUrl"
            :src="currentEvent.imageUrl"
            :alt="currentEvent.title"
            class="event-image"
          >
          <div v-else class="no-image">暂无相关图片</div>
        </div>
        <div class="audio-wrapper">
          <audio
            ref="audioPlayer"
            :src="currentEvent.audioUrl"
            controls
            class="audio-player"
          >
            您的浏览器不支持音频播放
          </audio>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMapStore } from '@/stores/map'
import { fetchEvents } from '@/services/api'

// 核心状态
const mapStore = useMapStore()
const loading = ref(false)
const error = ref(null)
const events = ref([])
const isCollapsed = ref(false)
const currentEvent = ref(null) // 当前选中事件
const audioPlayer = ref(null) // 音频DOM引用
const chaptersData = ref(null) // 章节数据

// 折叠/展开
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 事件类型颜色映射
const eventColors = {
  battle: '#dc2626',
  movement: '#3b82f6',
  occupation: '#16a34a',
  retreat: '#ef4444',
  city: '#2563eb',
  camp: '#16a34a'
}

// 获取事件颜色
const getEventColor = (type) => {
  return eventColors[type] || '#6b7280'
}

// 日期格式化
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 加载章节数据（chapters.json）
const loadChapters = async () => {
  try {
    const res = await fetch('/outline/chapters.json')
    chaptersData.value = await res.json()
  } catch (err) {
    console.error('加载章节数据失败:', err)
    error.value = '加载章节数据失败'
  }
}

// 匹配事件对应的章节信息
const getChapterByEventId = (eventId) => {
  if (!chaptersData.value?.chapters) return null
  return chaptersData.value.chapters.find(chapter =>
    chapter.event_ids?.includes(eventId)
  )
}

// 事件点击逻辑
const handleEventClick = (event) => {
  console.log('点击事件:', event)
  mapStore.setCurrentTime(event.date)

  // 停止当前播放的音频
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }

  // 匹配章节信息
  const chapter = getChapterByEventId(event.id)
  if (chapter) {
    currentEvent.value = {
      id: chapter.id,
      title: chapter.title,
      imageUrl: chapter.image?.url || '',
      audioUrl: `/tts/kokoro/${chapter.id}.wav` // 音频路径匹配
    }
    // 自动播放音频（需浏览器允许用户交互后播放）
    setTimeout(() => {
      audioPlayer.value?.play().catch(err => {
        console.warn('自动播放失败（浏览器策略限制）:', err)
      })
    }, 100)
  } else {
    currentEvent.value = null
    console.warn(`未找到事件${event.id}对应的章节信息`)
  }
}

// 新增：退出事件详情
const exitEventDetail = () => {
  // 停止音频播放
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }
  // 清空当前选中事件，隐藏详情面板
  currentEvent.value = null
}

// 加载事件数据
const loadEvents = async () => {
  loading.value = true
  error.value = null

  try {
    const data = await fetchEvents({
      projection: mapStore.projection
    })

    // 处理事件数据
    events.value = data.features
      .filter(f => f.properties.date)
      .map(f => ({
        id: f.properties.id || f.properties.name,
        name: f.properties.name,
        date: new Date(f.properties.date),
        type: f.properties.type
      }))
      .sort((a, b) => a.date - b.date)
  } catch (err) {
    error.value = '加载事件数据失败'
    console.error('加载事件失败:', err)
  } finally {
    loading.value = false
  }
}

// 初始化加载
onMounted(async () => {
  await loadChapters() // 先加载章节数据
  await loadEvents()   // 再加载事件数据
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
  min-height: auto;
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

/* 事件容器：列表+详情横向布局 */
.events-container {
  display: flex;
  gap: 24px;
  flex: 1;
}

.events-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  max-height: 600px;
  overflow-y: auto;
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

/* 事件详情样式 */
.event-detail {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

/* 新增：详情头部样式 */
.event-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-detail-title {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}

/* 新增：退出按钮样式 */
.exit-btn {
  padding: 4px 10px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.exit-btn:hover {
  background: #dc2626;
}

.event-image-wrapper {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  overflow: hidden;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.event-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  color: #64748b;
  font-size: 14px;
}

.audio-wrapper {
  width: 100%;
}

.audio-player {
  width: 100%;
  outline: none;
}
</style>
