import { apiClient } from '@/shared/lib/apiClient'

async function getRisks(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/risks`, { signal })
  return data
}

export { getRisks }
