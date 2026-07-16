import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getProjectMembers, removeProjectMember } from '../api/projects'

function useProjectMembers(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'members'],
    queryFn: () => getProjectMembers(projectId),
    enabled: Boolean(projectId),
  })
}

function useRemoveProjectMember(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId) => removeProjectMember(projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] })
    },
  })
}

export { useProjectMembers, useRemoveProjectMember }
