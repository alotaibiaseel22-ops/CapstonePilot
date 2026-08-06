import { apiClient } from '@/shared/lib/apiClient'

async function getComments(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/comments`, { signal })
  return data
}

async function postComment(projectId, body) {
  const { data } = await apiClient.post(`/projects/${projectId}/comments`, { body })
  return data
}

async function deleteComment(projectId, commentId) {
  await apiClient.delete(`/projects/${projectId}/comments/${commentId}`)
}

export { getComments, postComment, deleteComment }
