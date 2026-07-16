import { X } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { useProjectInvitations, useRevokeInvitation } from '../hooks/useInvitations'

const statusTone = { pending: 'warning', accepted: 'success', revoked: 'default' }

function PendingInvitationsList({ projectId }) {
  const { data: invitations, isLoading } = useProjectInvitations(projectId)
  const revoke = useRevokeInvitation(projectId)

  const emailInvitations = (invitations ?? []).filter((invitation) => invitation.email)

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading invitations...</p>
  }

  if (emailInvitations.length === 0) {
    return <p className="text-sm text-muted-foreground">No email invitations sent yet.</p>
  }

  return (
    <div className="space-y-2">
      {emailInvitations.map((invitation) => (
        <div
          key={invitation.id}
          className="flex items-center justify-between gap-3 rounded-lg border border-border px-4 py-2.5"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-800">{invitation.email}</span>
            <Badge variant={statusTone[invitation.status]}>{invitation.status}</Badge>
          </div>
          {invitation.status === 'pending' && (
            <button
              type="button"
              onClick={() => revoke.mutate(invitation.id)}
              disabled={revoke.isPending}
              aria-label={`Revoke invitation to ${invitation.email}`}
              className="text-gray-400 hover:text-red-600 disabled:opacity-50"
            >
              <X className="size-4" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

export { PendingInvitationsList }
