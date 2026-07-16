import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  inviteByEmail,
  getOrCreateLinkInvitation,
  regenerateLinkInvitation,
  getProjectInvitations,
  revokeInvitation,
  resendInvitation,
} from '../api/invitations'

function useProjectInvitations(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'invitations'],
    queryFn: ({ signal }) => getProjectInvitations(projectId, signal),
    enabled: Boolean(projectId),
  })
}

function useInviteByEmail(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (emails) => inviteByEmail(projectId, emails),
    onSuccess: (_data, emails) => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
      toast.success(
        emails.length === 1 ? `Invitation sent to ${emails[0]}` : `${emails.length} invitations sent`,
      )
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not send the invitation.')
    },
  })
}

function useLinkInvitation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => getOrCreateLinkInvitation(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not load the invite link.')
    },
  })
}

function useRegenerateLinkInvitation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => regenerateLinkInvitation(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
      toast.success('Invite link regenerated — the old link no longer works')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not regenerate the link.')
    },
  })
}

function useResendInvitation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: resendInvitation,
    onSuccess: (invitation) => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
      toast.success(`Invitation resent to ${invitation.email}`)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not resend the invitation.')
    },
  })
}

function useRevokeInvitation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: revokeInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
      toast.success('Invitation cancelled')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not cancel the invitation.')
    },
  })
}

// Same revoke call as above, used for the shareable link instead of an email
// invite - kept separate only so it can show link-appropriate copy.
function useDisableLinkInvitation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: revokeInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
      toast.success('Invite link disabled')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not disable the link.')
    },
  })
}

export {
  useProjectInvitations,
  useInviteByEmail,
  useLinkInvitation,
  useRegenerateLinkInvitation,
  useResendInvitation,
  useRevokeInvitation,
  useDisableLinkInvitation,
}
