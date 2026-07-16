import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getTasks, updateTask } from '../api/milestones'

function useTasks(milestoneId, { enabled = true } = {}) {
  return useQuery({
    queryKey: ['milestones', milestoneId, 'tasks'],
    queryFn: () => getTasks(milestoneId),
    enabled: Boolean(milestoneId) && enabled,
  })
}

function useUpdateTaskStatus(milestoneId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, status }) => updateTask(taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', milestoneId, 'tasks'] })
    },
  })
}

export { useTasks, useUpdateTaskStatus }
