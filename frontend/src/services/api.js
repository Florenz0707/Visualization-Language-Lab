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
请基于以下信息分析1812年卫国战争（俄法战争）的特定时刻：

1. **时间**: ${params.date}
2. **坐标**: 经度 ${params.lon.toFixed(2)}, 纬度 ${params.lat.toFixed(2)} (东欧平原/俄罗斯西部)
3. **法军动向**: 正在 ${params.type}
4. **地形特征**: ${params.terrain_hint}

请生成一段简短精炼的战况分析（200字以内），请务必包含以下维度的辩证思考：

- **地形与季节气候**: 
  结合当时的月份（6-9月为夏秋，10-12月为冬），分析气温（酷热、泥泞或严寒）以及地形（河流、森林、平原）对法军的具体影响。

- **军事态势与成败分析**:
  如果是【进攻阶段】（10月中旬前）：
  请重点分析法军取得的**战术胜利**（如攻占关键城市、赢得战斗、推进速度快）以及**成功的原因**（如拿破仑的指挥艺术、法军的高昂士气）。同时，辩证地指出潜在的**战略隐患**（如补给线拉长、非战斗减员）。**不要一味强调困难，要体现法军前期的强势。**
  
  如果是【撤退阶段】（10月中旬后）：
  请分析导致法军**失败或崩溃的核心原因**（是俄军的游击战、焦土政策，还是极端天气？），以及法军在绝境中的突围努力。

- **历史评述**: 
  用一句话总结这一刻对整个战争走向的关键意义。

语调要求：沉稳、专业，类似历史纪录片旁白，既要看到胜利的光辉，也要看到失败的阴影。
    `.trim()

    const result = await apiClient.post('/api/llm/chat', {
      message: '你是一位精通1812年拿破仑俄法战争的军事历史学家。请结合时间、地点、地形和气候，对法军的战况进行客观、辩证的深度分析。',
      system_prompt: prompt
    })

    console.log('LLM response:', result)

    return {
      analysis: result.data.response || '分析完成'
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