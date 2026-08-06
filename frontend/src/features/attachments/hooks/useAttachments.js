import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { deleteAttachment, getAttachments, uploadAttachment } from '../api/attachments'

function useAttachments(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'attachments'],
    queryFn: ({ signal }) => getAttachments(projectId, signal),
    enabled: Boolean(projectId),
  })
}

function useUploadAttachment(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file) => uploadAttachment(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'attachments'] })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not upload this file.')
    },
  })
}

function useDeleteAttachment(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (attachmentId) => deleteAttachment(projectId, attachmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'attachments'] })
      toast.success('Attachment removed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not remove this attachment.')
    },
  })
}

export { useAttachments, useUploadAttachment, useDeleteAttachment }
