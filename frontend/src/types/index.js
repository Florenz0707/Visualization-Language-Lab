/**
 * @typedef {Object} TimeRange
 * @property {Date} start
 * @property {Date} end
 */

/**
 * @typedef {Object} CameraConfig
 * @property {[number, number]} center - [lng, lat]
 * @property {number} zoom
 * @property {number} pitch
 * @property {number} bearing
 */

/**
 * @typedef {Object} Chapter
 * @property {number} id
 * @property {string} title
 * @property {string} date
 * @property {number[]} event_ids
 * @property {CameraConfig} camera
 * @property {string} narrative
 * @property {Object} image
 * @property {string} image.url
 * @property {string} image.attribution
 */

/**
 * @typedef {Object} TroopStatistics
 * @property {Array<{date: string, count: number}>} french
 * @property {Array<{date: string, count: number}>} russian
 */

export {}
