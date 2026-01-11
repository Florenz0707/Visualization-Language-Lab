<template>
  <div v-if="storyStore.isStoryMode" class="story-mode-overlay">
    <div class="story-content">
      <div class="story-header">
        <h2 class="chapter-title">{{ currentChapter?.title }}</h2>
        <button @click="exitStory" class="close-btn">✕</button>
      </div>

      <div class="story-body">
        <div v-if="currentChapter?.image" class="story-image">
          <img :src="currentChapter.image.url" :alt="currentChapter.title" />
          <p class="image-attribution">{{ currentChapter.image.attribution }}</p>
        </div>

        <div class="story-narrative">
          <p>{{ currentChapter?.narrative }}</p>
        </div>

        <audio
          v-if="audioUrl"
          ref="audioPlayer"
          :src="audioUrl"
          @ended="onAudioEnded"
        ></audio>
      </div>

      <div class="story-controls">
        <button
          @click="previousChapter"
          :disabled="!storyStore.hasPreviousChapter"
          class="nav-btn"
        >
          ← 上一章
        </button>

        <button @click="toggleAutoPlay" class="play-btn">
          {{ storyStore.isAutoPlaying ? '⏸ 暂停' : '▶ 播放' }}
        </button>

        <button
          @click="nextChapter"
          :disabled="!storyStore.hasNextChapter"
          class="nav-btn"
        >
          下一章 →
        </button>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: storyStore.progress + '%' }"></div>
      </div>
    </div>
  </div>

  <button
    v-else
    @click="enterStory"
    class="story-mode-btn"
  >
    📖 故事模式
  </button>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useStoryStore } from '@/stores/story'
import { useMapStore } from '@/stores/map'
import { fetchStoryOutline, getTTSAudioUrl } from '@/services/api'

const storyStore = useStoryStore()
const mapStore = useMapStore()
const audioPlayer = ref(null)

const currentChapter = computed(() => storyStore.currentChapter)

const audioUrl = computed(() => {
  if (!currentChapter.value) return null
  return getTTSAudioUrl(currentChapter.value.id)
})

const enterStory = async () => {
  try {
    const outline = await fetchStoryOutline()
    storyStore.setStoryOutline(outline)
    storyStore.enterStoryMode()
    updateMapForChapter()
  } catch (error) {
    console.error('Error loading story outline:', error)
  }
}

const exitStory = () => {
  storyStore.exitStoryMode()
  if (audioPlayer.value) {
    audioPlayer.value.pause()
  }
}

const nextChapter = () => {
  if (storyStore.nextChapter()) {
    updateMapForChapter()
  }
}

const previousChapter = () => {
  if (storyStore.previousChapter()) {
    updateMapForChapter()
  }
}

const toggleAutoPlay = () => {
  storyStore.toggleAutoPlay()
}

const onAudioEnded = () => {
  if (storyStore.isAutoPlaying) {
    nextChapter()
  }
}

const updateMapForChapter = () => {
  const chapter = currentChapter.value
  if (!chapter || !mapStore.mapInstance) return

  // Update map camera (Leaflet API)
  if (chapter.camera) {
    // Leaflet uses [lat, lng] format
    const center = [chapter.camera.center[1], chapter.camera.center[0]]
    mapStore.mapInstance.flyTo(center, chapter.camera.zoom, {
      duration: 2
    })
  }

  // Update time
  if (chapter.date) {
    mapStore.setCurrentTime(new Date(chapter.date))
  }

  // Play audio
  if (audioPlayer.value) {
    audioPlayer.value.play().catch(err => {
      console.warn('Audio autoplay prevented:', err)
    })
  }
}

watch(() => storyStore.isAutoPlaying, (isPlaying) => {
  if (isPlaying && audioPlayer.value) {
    audioPlayer.value.play()
  } else if (audioPlayer.value) {
    audioPlayer.value.pause()
  }
})

watch(() => currentChapter.value, () => {
  if (currentChapter.value && audioPlayer.value) {
    audioPlayer.value.load()
  }
})
</script>

<style scoped>
.story-mode-btn {
  position: fixed;
  top: 30px;
  left: 30px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  padding: 14px 24px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
  z-index: 1000;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.story-mode-btn:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(139, 92, 246, 0.5);
}

.story-mode-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.92);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.story-content {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.4s ease;
  border: 1px solid rgba(255, 255, 255, 0.8);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.story-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px 36px;
  border-bottom: 2px solid rgba(226, 232, 240, 0.6);
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.5));
}

.chapter-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.close-btn {
  background: rgba(100, 116, 139, 0.1);
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  transform: rotate(90deg);
}

.story-body {
  padding: 36px;
}

.story-image {
  margin-bottom: 28px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.story-image img {
  width: 100%;
  max-height: 400px;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.story-image:hover img {
  transform: scale(1.02);
}

.image-attribution {
  margin-top: 12px;
  font-size: 13px;
  color: #64748b;
  text-align: center;
  font-style: italic;
}

.story-narrative {
  font-size: 17px;
  line-height: 1.9;
  color: #334155;
  background: rgba(255, 255, 255, 0.6);
  padding: 24px;
  border-radius: 12px;
  border-left: 4px solid #8b5cf6;
}

.story-controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px 36px;
  border-top: 2px solid rgba(226, 232, 240, 0.6);
  background: rgba(248, 250, 252, 0.5);
}

.nav-btn, .play-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.nav-btn {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #475569;
}

.nav-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.play-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  min-width: 120px;
}

.play-btn:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4);
}

.progress-bar {
  height: 6px;
  background: linear-gradient(to right, #e2e8f0 0%, #cbd5e1 100%);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%);
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
}
</style>
