import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useStoryStore = defineStore('story', () => {
  // State
  const chapters = ref([])
  const currentChapterIndex = ref(0)
  const isStoryMode = ref(false)
  const isAutoPlaying = ref(false)
  const storyOutline = ref(null)

  // Computed
  const currentChapter = computed(() => {
    return chapters.value[currentChapterIndex.value] || null
  })

  const hasNextChapter = computed(() => {
    return currentChapterIndex.value < chapters.value.length - 1
  })

  const hasPreviousChapter = computed(() => {
    return currentChapterIndex.value > 0
  })

  const progress = computed(() => {
    if (chapters.value.length === 0) return 0
    return ((currentChapterIndex.value + 1) / chapters.value.length) * 100
  })

  // Actions
  const setChapters = (chapterList) => {
    chapters.value = chapterList
  }

  const setStoryOutline = (outline) => {
    storyOutline.value = outline
    if (outline && outline.chapters) {
      chapters.value = outline.chapters
    }
  }

  const setCurrentChapterIndex = (index) => {
    if (index >= 0 && index < chapters.value.length) {
      currentChapterIndex.value = index
    }
  }

  const nextChapter = () => {
    if (hasNextChapter.value) {
      currentChapterIndex.value++
      return true
    }
    return false
  }

  const previousChapter = () => {
    if (hasPreviousChapter.value) {
      currentChapterIndex.value--
      return true
    }
    return false
  }

  const enterStoryMode = () => {
    isStoryMode.value = true
    currentChapterIndex.value = 0
  }

  const exitStoryMode = () => {
    isStoryMode.value = false
    isAutoPlaying.value = false
  }

  const toggleAutoPlay = () => {
    isAutoPlaying.value = !isAutoPlaying.value
  }

  const setAutoPlaying = (playing) => {
    isAutoPlaying.value = playing
  }

  return {
    // State
    chapters,
    currentChapterIndex,
    isStoryMode,
    isAutoPlaying,
    storyOutline,
    // Computed
    currentChapter,
    hasNextChapter,
    hasPreviousChapter,
    progress,
    // Actions
    setChapters,
    setStoryOutline,
    setCurrentChapterIndex,
    nextChapter,
    previousChapter,
    enterStoryMode,
    exitStoryMode,
    toggleAutoPlay,
    setAutoPlaying
  }
})
