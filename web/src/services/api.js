const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

/**
 * @typedef {Object} AuditArea
 * @property {number} id
 * @property {string} description
 * @property {Object} geometry
 * @property {number} areaSquareMeters
 * @property {string} createdAt
 */

/**
 * @description GET /api/audit-areas
 * @param {string} [capturedAt]
 * @returns {Promise<Array<AuditArea>>}
 */
export async function listAuditAreas(capturedAt) {
  const url = capturedAt ? `${baseURL}/api/audit-areas?capturedAt=${capturedAt}` : `${baseURL}/api/audit-areas`;
  const response = await fetch(url);
  const data = await response.json();
  return data;
}

/**
 * @description POST /api/audit-areas
 * @param {Object} data
 * @param {string} data.description
 * @param {Object} data.geometry
 * @returns {Promise<AuditArea>}
 */
export async function createAuditArea(data) {
  const response = await fetch(`${baseURL}/api/audit-areas`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  const json = await response.json();
  return json;
}