import { apiClient } from '@/shared/lib/apiClient'

async function getProjects(signal) {
  const { data } = await apiClient.get('/projects', { signal })
  return data
}

async function getProjectById(id, signal) {
  const { data } = await apiClient.get(`/projects/${id}`, { signal })
  return data
}

async function createProject(payload) {
  const { data } = await apiClient.post('/projects', payload)
  return data
}

async function updateProject(id, payload) {
  const { data } = await apiClient.patch(`/projects/${id}`, payload)
  return data
}

async function deleteProject(id) {
  await apiClient.delete(`/projects/${id}`)
}

async function getProjectMembers(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/members`, { signal })
  return data
}

async function removeProjectMember(projectId, userId) {
  await apiClient.delete(`/projects/${projectId}/members/${userId}`)
}

async function getProjectGuests(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/guests`, { signal })
  return data
}

async function generatePlan(projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post(`/projects/${projectId}/plan/generate`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export {
  getProjects,
  getProjectById,
  createProject,
  updateProject,
  deleteProject,
  getProjectMembers,
  removeProjectMember,
  getProjectGuests,
  generatePlan,
}
