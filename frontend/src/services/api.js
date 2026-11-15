/**
 * PipelineAI - Frontend API Service Client
 * Handles communication with backend Flask endpoints with robust error handling.
 */

const BASE_URL = window.location.origin;

async function safeFetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (err) {
    throw new Error(`Server returned non-JSON response (${res.status}): ${text.slice(0, 100)}`);
  }
  if (!res.ok) {
    throw new Error(data.message || `Request failed with status ${res.status}`);
  }
  return data;
}

export const ApiService = {
  async checkHealth() {
    try {
      return await safeFetchJson(`${BASE_URL}/api/health`);
    } catch (err) {
      console.warn("Backend not reachable directly, returning offline status:", err);
      return { status: "offline", error: err.message };
    }
  },

  async predictSingle(pc, history, predictor = "xgboost") {
    return await safeFetchJson(`${BASE_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pc, history, predictor })
    });
  },

  async runSimulation(traceId = 0, predictor = "xgboost", sampleLimit = 100, penalty = 2) {
    return await safeFetchJson(`${BASE_URL}/api/simulate/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        trace_id: traceId,
        predictor,
        sample_limit: sampleLimit,
        penalty
      })
    });
  },

  async comparePredictors(traceId = 0, sampleLimit = 200) {
    return await safeFetchJson(`${BASE_URL}/api/simulate/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trace_id: traceId, sample_limit: sampleLimit })
    });
  },

  async getMetrics() {
    return await safeFetchJson(`${BASE_URL}/api/analytics/metrics`);
  },

  async getMetadata() {
    return await safeFetchJson(`${BASE_URL}/api/analytics/metadata`);
  },

  async getTraces() {
    return await safeFetchJson(`${BASE_URL}/api/analytics/traces`);
  },

  async getTraceDetails(traceId = 0, limit = 50, offset = 0) {
    return await safeFetchJson(`${BASE_URL}/api/analytics/traces/${traceId}?limit=${limit}&offset=${offset}`);
  }
};
