import { apiClient } from '@/shared/lib/apiClient'
import { guestApiClient } from '@/shared/lib/guestApiClient'

// guestJoin/getGuestSession use the plain apiClient - guestJoin needs no
// auth header at all (it's how a guest token is first obtained), and
// getGuestSession authenticates with whatever stored token the caller
// passes explicitly, not via guestApiClient's per-invitation localStorage
// lookup (there may be nothing stored yet, which is exactly the case this
// gets called to check).
async function guestJoin(invitationToken, displayName) {
  const { data } = await apiClient.post(`/invitations/${invitationToken}/guest-join`, {
    display_name: displayName,
  })
  return data
}

async function getGuestSession(invitationToken, guestAccessToken) {
  const { data } = await apiClient.get(`/invitations/${invitationToken}/guest-session`, {
    headers: { Authorization: `Bearer ${guestAccessToken}` },
  })
  return data
}

async function getGuestProject(invitationToken, projectId) {
  const { data } = await guestApiClient.get(`/projects/${projectId}`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function getGuestMembers(invitationToken, projectId) {
  const { data } = await guestApiClient.get(`/projects/${projectId}/members`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function getGuestGuests(invitationToken, projectId) {
  const { data } = await guestApiClient.get(`/projects/${projectId}/guests`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function getGuestMilestones(invitationToken, projectId) {
  const { data } = await guestApiClient.get(`/projects/${projectId}/milestones`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function getGuestTasks(invitationToken, milestoneId) {
  const { data } = await guestApiClient.get(`/milestones/${milestoneId}/tasks`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function updateGuestTaskStatus(invitationToken, taskId, statusValue) {
  const { data } = await guestApiClient.patch(
    `/tasks/${taskId}/status`,
    { status: statusValue },
    { guestInvitationToken: invitationToken },
  )
  return data
}

async function getGuestAttachments(invitationToken, projectId) {
  const { data } = await guestApiClient.get(`/projects/${projectId}/attachments`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function uploadGuestAttachment(invitationToken, projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await guestApiClient.post(`/projects/${projectId}/attachments`, formData, {
    guestInvitationToken: invitationToken,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

async function downloadGuestAttachment(invitationToken, projectId, attachmentId) {
  const { data } = await guestApiClient.get(
    `/projects/${projectId}/attachments/${attachmentId}/download`,
    { guestInvitationToken: invitationToken, responseType: 'blob' },
  )
  return data
}

async function deleteGuestAttachment(invitationToken, projectId, attachmentId) {
  await guestApiClient.delete(`/projects/${projectId}/attachments/${attachmentId}`, {
    guestInvitationToken: invitationToken,
  })
}

async function getGuestComments(invitationToken, projectId) {
  const { data } = await guestApiClient.get(`/projects/${projectId}/comments`, {
    guestInvitationToken: invitationToken,
  })
  return data
}

async function postGuestComment(invitationToken, projectId, body) {
  const { data } = await guestApiClient.post(
    `/projects/${projectId}/comments`,
    { body },
    { guestInvitationToken: invitationToken },
  )
  return data
}

async function deleteGuestComment(invitationToken, projectId, commentId) {
  await guestApiClient.delete(`/projects/${projectId}/comments/${commentId}`, {
    guestInvitationToken: invitationToken,
  })
}

export {
  guestJoin,
  getGuestSession,
  getGuestProject,
  getGuestMembers,
  getGuestGuests,
  getGuestMilestones,
  getGuestTasks,
  updateGuestTaskStatus,
  getGuestAttachments,
  uploadGuestAttachment,
  downloadGuestAttachment,
  deleteGuestAttachment,
  getGuestComments,
  postGuestComment,
  deleteGuestComment,
}
