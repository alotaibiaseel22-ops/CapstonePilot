import { apiClient } from '@/shared/lib/apiClient'

async function getMilestones(projectId) {
  const { data } = await apiClient.get(`/projects/${projectId}/milestones`)
  return data
}

async function createMilestone(projectId, payload) {
  const { data } = await apiClient.post(`/projects/${projectId}/milestones`, payload)
  return data
}

async function getTasks(milestoneId) {
  const { data } = await apiClient.get(`/milestones/${milestoneId}/tasks`)
  return data
}

async function createTask(milestoneId, payload) {
  const { data } = await apiClient.post(`/milestones/${milestoneId}/tasks`, payload)
  return data
}

async function updateTask(taskId, payload) {
  const { data } = await apiClient.patch(`/tasks/${taskId}`, payload)
  return data
}

export { getMilestones, createMilestone, getTasks, createTask, updateTask }
