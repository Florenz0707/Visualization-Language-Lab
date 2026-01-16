<template>
  <div class="story-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-header">
      <h3 class="title">故事讲述</h3>
      <div class="header-actions">
        <div class="status-badge" v-if="!isCollapsed">
          <span v-if="currentChapter">{{ currentChapter.title }}</span>
          <span v-else>暂无事件</span>
        </div>
        <button @click="toggleCollapse" class="collapse-btn" :title="isCollapsed ? '展开' : '折叠'">
          {{ isCollapsed ? '▶' : '◀' }}
        </button>
      </div>
    </div>

    <div v-if="!isCollapsed && !currentChapter" class="empty">
      <span>点击事件序列中的事件查看故事</span>
    </div>

    <div v-else-if="!isCollapsed && currentChapter" class="story-content">
      <!-- 事件标题 -->
      <div class="story-title">
        <h4>{{ currentChapter.title }}</h4>
        <div class="story-date">{{ formatDate(currentChapter.date) }}</div>
      </div>

      <!-- 历史画作 -->
      <div v-if="currentChapter.image" class="story-image-wrapper">
        <img
          :src="currentChapter.image.url"
          :alt="currentChapter.title"
          class="story-image"
        >
      </div>

      <!-- 故事文本 -->
      <div class="story-narrative">
        <p>{{ currentChapter.narrative }}</p>
      </div>

      <!-- 音频播放控制 -->
      <div class="audio-controls">
        <button @click="toggleAudio" class="audio-btn">
          {{ isPlaying ? '⏸ 暂停' : '▶ 播放' }}
        </button>
        <audio
          ref="audioPlayer"
          :src="audioUrl"
          @play="isPlaying = true"
          @pause="isPlaying = false"
          @ended="isPlaying = false"
        ></audio>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useMapStore } from '@/stores/map'

const mapStore = useMapStore()
const isCollapsed = ref(false)
const currentChapter = ref(null)
const chaptersData = ref(null)
const audioPlayer = ref(null)
const isPlaying = ref(false)

// 折叠切换
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  // 折叠时暂停音频
  if (isCollapsed.value && audioPlayer.value) {
    audioPlayer.value.pause()
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

// 音频URL
const audioUrl = computed(() => {
  if (!currentChapter.value) return null
  return `/tts/kokoro/${currentChapter.value.id}.wav`
})

// 播放/暂停音频
const toggleAudio = () => {
  if (!audioPlayer.value) return

  if (isPlaying.value) {
    audioPlayer.value.pause()
  } else {
    audioPlayer.value.play().catch(err => {
      console.warn('音频播放失败:', err)
    })
  }
}

// 加载章节数据
const loadChapters = async () => {
  try {
    const res = await fetch('/outline/chapters.json')
    chaptersData.value = await res.json()
  } catch (err) {
    console.error('加载章节数据失败:', err)
  }
}

// 根据事件ID查找章节
const getChapterByEventId = (eventId) => {
  if (!chaptersData.value?.chapters) return null
  return chaptersData.value.chapters.find(chapter =>
    chapter.event_ids?.includes(eventId)
  )
}

// 更新当前显示的最近已发生事件
const updateCurrentChapter = () => {
  if (!chaptersData.value?.chapters) return

  const currentTime = mapStore.currentTime.getTime()

  // 找到所有已发生的事件（日期 <= 当前时间）
  const pastChapters = chaptersData.value.chapters.filter(chapter => {
    const chapterTime = new Date(chapter.date).getTime()
    return chapterTime <= currentTime
  })

  // 选择最近的一个
  if (pastChapters.length > 0) {
    currentChapter.value = pastChapters[pastChapters.length - 1]
  } else {
    currentChapter.value = null
  }
}

// 监听时间变化，自动更新显示的章节
watch(() => mapStore.currentTime, () => {
  updateCurrentChapter()
}, { deep: true })

// 组件挂载时加载数据
onMounted(() => {
  loadChapters()
})

// 组件卸载时清理音频
onUnmounted(() => {
  if (audioPlayer.value) {
    audioPlayer.value.pause()
  }
})
</script>

<style scoped>
.story-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  transition: all 0.3s ease;
  max-height: 80vh;
  overflow-y: auto;
}

.story-panel.collapsed {
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
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.empty {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

.story-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.story-title h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.story-date {
  font-size: 13px;
  color: #64748b;
}

.story-image-wrapper {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.story-image {
  width: 100%;
  height: auto;
  display: block;
  object-fit: cover;
}

.story-narrative {
  font-size: 14px;
  line-height: 1.8;
  color: #334155;
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
}

.story-narrative p {
  margin: 0;
}

.audio-controls {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

.audio-btn {
  padding: 10px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.audio-btn:hover {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

audio {
  display: none;
}
</style>
