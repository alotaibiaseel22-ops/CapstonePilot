import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  inviteByEmail,
  getOrCreateLinkInvitation,
  getProjectInvitations,
  revokeInvitation,
} from '../api/invitations'

function useProjectInvitations(projectId) {
  return useQuery({
    queryKey: ['projects', projectId, 'invitations'],
    queryFn: () => getProjectInvitations(projectId),
    enabled: Boolean(projectId),
  })
}

function useInviteByEmail(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (emails) => inviteByEmail(projectId, emails),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
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
  })
}

function useRevokeInvitation(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: revokeInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
    },
  })
}

export { useProjectInvitations, useInviteByEmail, useLinkInvitation, useRevokeInvitation }
