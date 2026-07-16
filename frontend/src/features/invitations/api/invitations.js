import { apiClient } from '@/shared/lib/apiClient'

async function inviteByEmail(projectId, emails) {
  const { data } = await apiClient.post(`/projects/${projectId}/invitations`, { emails })
  return data
}

async function getOrCreateLinkInvitation(projectId) {
  const { data } = await apiClient.post(`/projects/${projectId}/invitations/link`)
  return data
}

async function regenerateLinkInvitation(projectId) {
  const { data } = await apiClient.post(`/projects/${projectId}/invitations/link/regenerate`)
  return data
}

async function getProjectInvitations(projectId, signal) {
  const { data } = await apiClient.get(`/projects/${projectId}/invitations`, { signal })
  return data
}

async function revokeInvitation(invitationId) {
  await apiClient.delete(`/invitations/${invitationId}`)
}

async function resendInvitation(invitationId) {
  const { data } = await apiClient.post(`/invitations/${invitationId}/resend`)
  return data
}

async function getMyInvitations() {
  const { data } = await apiClient.get('/invitations/mine')
  return data
}

async function acceptInvitation(token) {
  const { data } = await apiClient.post(`/invitations/${token}/accept`)
  return data
}

async function getInvitationPreview(token) {
  const { data } = await apiClient.get(`/invitations/${token}/preview`)
  return data
}

export {
  inviteByEmail,
  getOrCreateLinkInvitation,
  regenerateLinkInvitation,
  getProjectInvitations,
  revokeInvitation,
  resendInvitation,
  getMyInvitations,
  acceptInvitation,
  getInvitationPreview,
}
