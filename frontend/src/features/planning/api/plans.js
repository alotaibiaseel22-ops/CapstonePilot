import { apiClient } from '@/shared/lib/apiClient'

async function getPlan(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/plan`, { signal })
  return data
}

async function approvePlan(projectId) {
  const { data } = await apiClient.post(`/projects/${projectId}/plan/approve`)
  return data
}

async function rejectPlan(projectId) {
  const { data } = await apiClient.post(`/projects/${projectId}/plan/reject`)
  return data
}

export { getPlan, approvePlan, rejectPlan }
