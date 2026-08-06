import { useQuery } from '@tanstack/react-query'
import { getProjectGuests } from '../api/projects'

function useProjectGuests(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'guests'],
    queryFn: ({ signal }) => getProjectGuests(projectId, signal),
    enabled: Boolean(projectId),
  })
}

export { useProjectGuests }
