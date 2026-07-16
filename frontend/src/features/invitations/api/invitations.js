import { apiClient } from '@/shared/lib/apiClient'

async function inviteByEmail(projectId, emails) {
  const { data } = await apiClient.post(`/projects/${projectId}/invitations`, { emails })
  return data
}

async function getOrCreateLinkInvitation(projectId) {
  const { data } = await apiClient.post(`/projects/${projectId}/invitations/link`)
  return data
}

async function getProjectInvitations(projectId) {
  const { data } = await apiClient.get(`/projects/${projectId}/invitations`)
  return data
}

async function revokeInvitation(invitationId) {
  await apiClient.delete(`/invitations/${invitationId}`)
}

async function getMyInvitations() {
  const { data } = await apiClient.get('/invitations/mine')
  return data
}

async function acceptInvitation(token) {
  const { data } = await apiClient.post(`/invitations/${token}/accept`)
  return data
}

export {
  inviteByEmail,
  getOrCreateLinkInvitation,
  getProjectInvitations,
  revokeInvitation,
  getMyInvitations,
  acceptInvitation,
}
