import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

/**
 * Fetch events GeoJSON
 * @param {Object} params
 * @param {string} [params.start] - Start date (YYYY-MM-DD)
 * @param {string} [params.end] - End date (YYYY-MM-DD)
 * @param {string} [params.bbox] - Bounding box (minx,miny,maxx,maxy)
 * @param {string} [params.projection] - Projection type (wgs84, webmercator, lambert)
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export const fetchEvents = async (params = {}) => {
  const response = await apiClient.get('/api/events', { params })
  return response.data
}

/**
 * Fetch movements GeoJSON
 * @param {Object} params
 * @param {string} [params.projection] - Projection type
 * @param {string} [params.bbox] - Bounding box
 * @param {boolean} [params.simplify] - Apply simplification
 * @param {number} [params.tolerance] - Simplification tolerance
 * @param {number} [params.lod] - Level of detail (1-7)
 * @param {number} [params.zoom] - Map zoom level
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export const fetchMovements = async (params = {}) => {
  const response = await apiClient.get('/api/movements', { params })
  return response.data
}

/**
 * Fetch territories GeoJSON
 * @param {Object} params
 * @param {string} [params.projection] - Projection type
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export const fetchTerritories = async (params = {}) => {
  const response = await apiClient.get('/api/territories', { params })
  return response.data
}

/**
 * Fetch flow data for flow map
 * @param {Object} params
 * @param {boolean} [params.simplify] - Apply simplification
 * @param {number} [params.threshold] - Simplification threshold
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export const fetchFlows = async (params = {}) => {
  const response = await apiClient.get('/api/flows', { params })
  return response.data
}

/**
 * Fetch troop statistics
 * @param {Object} params
 * @param {string} params.start - Start date (YYYY-MM-DD)
 * @param {string} params.end - End date (YYYY-MM-DD)
 * @param {string} [params.faction] - Faction filter (french, russian)
 * @param {string} [params.period] - Aggregation period (month, week, day)
 * @returns {Promise<Object>} Statistics data
 */
export const fetchTroopStatistics = async (params) => {
  const response = await apiClient.get('/api/statistics/troops', { params })
  return response.data
}

/**
 * Fetch story mode outline
 * @param {number} [chapterId] - Optional chapter ID
 * @returns {Promise<Object>} Story outline data
 */
export const fetchStoryOutline = async (chapterId = null) => {
  const params = chapterId ? { chapter_id: chapterId } : {}
  const response = await apiClient.get('/api/story/outline', { params })
  return response.data
}

/**
 * Get TTS audio URL for a chapter
 * @param {number} chapterId - Chapter ID
 * @returns {string} Audio URL
 */
export const getTTSAudioUrl = (chapterId) => {
  return `${API_BASE_URL}/api/story/tts/${chapterId}`
}

/**
 * Analyze route using LLM
 * @param {Object} params
 * @param {number} params.lat - Latitude
 * @param {number} params.lon - Longitude
 * @param {string} params.date - Date
 * @param {string} params.type - Type (进攻/撤退)
 * @param {string} params.terrain_hint - Terrain hint
 * @returns {Promise<Object>} Analysis result
 */
export const analyzeRoute = async (params) => {
  try {
    const prompt = `
请分析以下战况：
1. **时间**: ${params.date}
2. **坐标**: 经度 ${params.lon.toFixed(2)}, 纬度 ${params.lat.toFixed(2)} (东欧平原/俄罗斯西部)
3. **状态**: 法军正在 ${params.type}
4. **地形参考**: ${params.terrain_hint}

请生成一段简短的分析（200字以内），内容包括：
- **地理环境**: 该位置附近是否有重要河流（如别列津纳河、第聂伯河）或特殊地形？
- **军事态势**: 此时法军面临的主要困难是什么？
- **历史意义**: 这一阶段对战争成败有何影响？

请用沉稳、专业的历史纪录片旁白口吻回答。
    `.trim()

    const response = await apiClient.post('/api/llm/chat', {
      messages: [
        {
          role: 'system',
          content: '你是一位精通1812年拿破仑俄法战争的军事历史学家和地理学家。请基于用户提供的坐标、时间和地形数据进行专业分析。'
        },
        {
          role: 'user',
          content: prompt
        }
      ]
    })

    return {
      analysis: response.data.content || response.data.message || '分析完成'
    }
  } catch (error) {
    console.error('API call failed:', error)
    throw new Error('无法连接到后端服务，请确认服务已启动')
  }
}

export default {
  fetchEvents,
  fetchMovements,
  fetchTerritories,
  fetchFlows,
  fetchTroopStatistics,
  fetchStoryOutline,
  getTTSAudioUrl,
  analyzeRoute
}
