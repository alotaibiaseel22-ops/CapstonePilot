import { apiClient } from '@/shared/lib/apiClient'

async function getActivity(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/activity`, { signal })
  return data
}

async function getUnreadCount(signal) {
  const { data } = await apiClient.get('/notifications/unread-count', { signal })
  return data
}

async function markSeen() {
  const { data } = await apiClient.post('/notifications/mark-seen')
  return data
}

export { getActivity, getUnreadCount, markSeen }
