import { useQuery } from '@tanstack/react-query'
import { getJob } from '../api/jobs'

const TERMINAL_STATUSES = new Set(['succeeded', 'failed'])

function useJobStatus(jobId) {
  return useQuery({
    queryKey: ['jobs', jobId],
    queryFn: () => getJob(jobId),
    enabled: Boolean(jobId),
    refetchInterval: (query) => (TERMINAL_STATUSES.has(query.state.data?.status) ? false : 2000),
  })
}

export { useJobStatus }
