import { apiClient } from '@/shared/lib/apiClient'

async function getJob(jobId) {
  const { data } = await apiClient.get(`/jobs/${jobId}`)
  return data
}

export { getJob }
