import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { assignTask, getTasks, updateTask } from '../api/milestones'

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

function useAssignTask(milestoneId) {
  const queryClient = useQueryClient()
  return useMutation({
    // assigneeId/assigneeGuestId default to null (not undefined) so
    // omitting one when setting the other still sends an explicit null -
    // assignTask's dedicated endpoint always applies both fields as given,
    // so an omitted/undefined field would otherwise be dropped by axios
    // rather than clearing the other assignee type server-side.
    mutationFn: ({ taskId, assigneeId = null, assigneeGuestId = null }) =>
      assignTask(taskId, { assignee_id: assigneeId, assignee_guest_id: assigneeGuestId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', milestoneId, 'tasks'] })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not update the assignee.')
    },
  })
}

export { useTasks, useUpdateTaskStatus, useAssignTask }
