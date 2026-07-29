import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  approveRecommendation,
  getRecommendations,
  rejectRecommendation,
} from '../api/recommendations'

function useRecommendations(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'recommendations'],
    queryFn: ({ signal }) => getRecommendations(projectId, signal),
    enabled: Boolean(projectId),
  })
}

function useApproveRecommendation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: approveRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'recommendations'] })
      toast.success('Recommendation accepted')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not accept the recommendation.')
    },
  })
}

function useRejectRecommendation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: rejectRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'recommendations'] })
      toast.success('Recommendation dismissed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not dismiss the recommendation.')
    },
  })
}

export { useRecommendations, useApproveRecommendation, useRejectRecommendation }
