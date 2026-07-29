import { apiClient } from '@/shared/lib/apiClient'

async function getRecommendations(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/recommendations`, { signal })
  return data
}

async function approveRecommendation(recommendationId) {
  const { data } = await apiClient.post(`/recommendations/${recommendationId}/approve`)
  return data
}

async function rejectRecommendation(recommendationId) {
  const { data } = await apiClient.post(`/recommendations/${recommendationId}/reject`)
  return data
}

export { getRecommendations, approveRecommendation, rejectRecommendation }
