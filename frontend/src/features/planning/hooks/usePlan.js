import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { approvePlan, getPlan, rejectPlan } from '../api/plans'

function usePlan(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'plan'],
    queryFn: ({ signal }) => getPlan(projectId, signal),
    enabled: Boolean(projectId),
  })
}

function useApprovePlan(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => approvePlan(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'plan'] })
      toast.success('Plan approved')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not approve the plan.')
    },
  })
}

function useRejectPlan(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => rejectPlan(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'plan'] })
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'milestones'] })
      toast.success('Plan rejected')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not reject the plan.')
    },
  })
}

export { usePlan, useApprovePlan, useRejectPlan }
