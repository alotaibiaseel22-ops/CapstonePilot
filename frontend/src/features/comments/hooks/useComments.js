import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { deleteComment, getComments, postComment } from '../api/comments'

function useComments(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'comments'],
    queryFn: ({ signal }) => getComments(projectId, signal),
    enabled: Boolean(projectId),
  })
}

function usePostComment(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body) => postComment(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'comments'] })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not post this comment.')
    },
  })
}

function useDeleteComment(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (commentId) => deleteComment(projectId, commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'comments'] })
      toast.success('Comment removed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not remove this comment.')
    },
  })
}

export { useComments, usePostComment, useDeleteComment }
