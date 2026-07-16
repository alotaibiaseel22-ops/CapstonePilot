import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getProjectMembers, addProjectMember, removeProjectMember } from '../api/projects'

function useProjectMembers(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'members'],
    queryFn: () => getProjectMembers(projectId),
    enabled: Boolean(projectId),
  })
}

function useAddProjectMember(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (email) => addProjectMember(projectId, email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] })
    },
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

export { useProjectMembers, useAddProjectMember, useRemoveProjectMember }
