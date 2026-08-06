import { apiClient } from '@/shared/lib/apiClient'

async function getAttachments(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/attachments`, { signal })
  return data
}

async function uploadAttachment(projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post(`/projects/${projectId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

async function downloadAttachment(projectId, attachmentId) {
  const { data } = await apiClient.get(
    `/projects/${projectId}/attachments/${attachmentId}/download`,
    { responseType: 'blob' },
  )
  return data
}

async function deleteAttachment(projectId, attachmentId) {
  await apiClient.delete(`/projects/${projectId}/attachments/${attachmentId}`)
}

export { getAttachments, uploadAttachment, downloadAttachment, deleteAttachment }
