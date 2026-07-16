import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getProjectMembers, removeProjectMember } from '../api/projects'

function useProjectMembers(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'members'],
    queryFn: ({ signal }) => getProjectMembers(projectId, signal),
    enabled: Boolean(projectId),
  })
}

function useRemoveProjectMember(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId) => removeProjectMember(projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] })
      toast.success('Collaborator removed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not remove this collaborator.')
    },
  })
}

export { useProjectMembers, useRemoveProjectMember }
