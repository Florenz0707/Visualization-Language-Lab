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

export default {
  fetchEvents,
  fetchMovements,
  fetchTerritories,
  fetchFlows,
  fetchTroopStatistics,
  fetchStoryOutline,
  getTTSAudioUrl
}
