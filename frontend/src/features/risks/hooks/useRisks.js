import { useQuery } from '@tanstack/react-query'
import { getRisks } from '../api/risks'

function useRisks(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'risks'],
    queryFn: ({ signal }) => getRisks(projectId, signal),
    enabled: Boolean(projectId),
  })
}

export { useRisks }
