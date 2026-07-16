import { apiClient } from '@/shared/lib/apiClient'

async function getProjects() {
  const { data } = await apiClient.get('/projects')
  return data
}

async function getProjectById(id) {
  const { data } = await apiClient.get(`/projects/${id}`)
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

async function getProjectMembers(projectId) {
  const { data } = await apiClient.get(`/projects/${projectId}/members`)
  return data
}

async function addProjectMember(projectId, email) {
  const { data } = await apiClient.post(`/projects/${projectId}/members`, { email })
  return data
}

async function removeProjectMember(projectId, userId) {
  await apiClient.delete(`/projects/${projectId}/members/${userId}`)
}

async function analyzeProposal(projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post(`/projects/${projectId}/analyze-proposal`, formData, {
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
  addProjectMember,
  removeProjectMember,
  analyzeProposal,
}
