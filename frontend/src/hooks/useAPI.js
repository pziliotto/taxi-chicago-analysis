// src/hooks/useAPI.js
// Hook centralizado para todas as chamadas à FastAPI.
// Cada função retorna { data, loading, error } para uso nos componentes.

import { useState, useEffect } from 'react'
import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

// ── Hook genérico ─────────────────────────────────────────────
function useFetch(endpoint, params = {}) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const paramsKey = JSON.stringify(params)

  useEffect(() => {
    setLoading(true)
    setError(null)
    axios.get(`${BASE_URL}${endpoint}`, { params })
      .then(res => { setData(res.data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [endpoint, paramsKey])

  return { data, loading, error }
}

// ── Hooks específicos ─────────────────────────────────────────

export function useSummary() {
  return useFetch('/stats/summary')
}

export function useNeighborhoods() {
  return useFetch('/neighborhoods')
}

export function useNeighborhood(name) {
  return useFetch(name ? `/neighborhoods/${encodeURIComponent(name)}` : null)
}

export function useHourlyFlow(neighborhood = null, season = null) {
  const params = {}
  if (neighborhood) params.neighborhood = neighborhood
  if (season)       params.season = season
  return useFetch('/flow/hourly', params)
}

export function useWeeklyFlow(neighborhood = null) {
  const params = {}
  if (neighborhood) params.neighborhood = neighborhood
  return useFetch('/flow/weekly', params)
}

export function useSeasonalFlow() {
  return useFetch('/flow/seasonal')
}

export function useRushFlow() {
  return useFetch('/flow/rush')
}

export function useTopHexagons(limit = 20, metric = 'total_flow') {
  return useFetch('/hexagons/top', { limit, metric })
}

export function useCommunities() {
  return useFetch('/graph/communities')
}

export function useEdges(minWeight = 500) {
  return useFetch('/graph/edges', { min_weight: minWeight, limit: 200 })
}