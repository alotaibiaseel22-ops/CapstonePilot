import { useQuery } from '@tanstack/react-query'
import { getMilestones } from '../api/milestones'

function useMilestones(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'milestones'],
    queryFn: () => getMilestones(projectId),
    enabled: Boolean(projectId),
  })
}

export { useMilestones }
