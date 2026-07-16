import { useState } from 'react'
import { toast } from 'sonner'
import { ArrowRightLeft, Copy, MoreVertical, RotateCw, UserX, X } from 'lucide-react'
import { Modal } from '@/shared/components/ui/modal'
import { ConfirmDialog } from '@/shared/components/ui/confirm-dialog'
import { Badge } from '@/shared/components/ui/badge'
import { Avatar } from '@/shared/components/ui/avatar'
import { Button } from '@/shared/components/ui/button'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProjectMembers, useRemoveProjectMember } from '../hooks/useProjectMembers'
import {
  useProjectInvitations,
  useResendInvitation,
  useRevokeInvitation,
} from '@/features/invitations/hooks/useInvitations'
import { InviteByEmailForm } from '@/features/invitations/components/InviteByEmailForm'
import { InviteLinkCard } from '@/features/invitations/components/InviteLinkCard'

function initialsOf(text) {
  return text
    .split(/[\s@.]+/)
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function formatRelative(value) {
  const days = Math.floor((Date.now() - new Date(value).getTime()) / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'today'
  if (days === 1) return '1 day ago'
  return `${days} days ago`
}

function AccessRow({ name, email, badge, badgeVariant, menu }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5" data-testid="access-row">
      <div className="flex min-w-0 items-center gap-3">
        <Avatar initials={initialsOf(name || email)} className="shrink-0" />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-900">{name || email}</p>
          {name && <p className="truncate text-xs text-muted-foreground">{email}</p>}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Badge variant={badgeVariant}>{badge}</Badge>
        {menu}
      </div>
    </div>
  )
}

function ShareModal({ open, onClose, project }) {
  const { user } = useAuth()
  const isOwner = user?.id === project.owner_id

  const { data: members, isLoading: membersLoading } = useProjectMembers(project.id)
  const { data: invitations, isLoading: invitationsLoading } = useProjectInvitations(project.id)
  const removeMember = useRemoveProjectMember(project.id)
  const resendInvitation = useResendInvitation(project.id)
  const revokeInvitation = useRevokeInvitation(project.id)

  const [removingMember, setRemovingMember] = useState(null)
  const [cancellingInvitation, setCancellingInvitation] = useState(null)

  const linkInvitation = (invitations ?? []).find(
    (invitation) => !invitation.email && invitation.status === 'pending',
  )
  // Whether a link invitation has EVER existed for this project (active or
  // revoked) - once the owner disables it, one should never auto-recreate.
  const linkEverExisted = (invitations ?? []).some((invitation) => !invitation.email)
  const pendingEmailInvitations = isOwner
    ? (invitations ?? []).filter((invitation) => invitation.email && invitation.status === 'pending')
    : []

  async function handleConfirmRemove() {
    await removeMember.mutateAsync(removingMember.user_id)
    setRemovingMember(null)
  }

  async function handleConfirmCancel() {
    await revokeInvitation.mutateAsync(cancellingInvitation.id)
    setCancellingInvitation(null)
  }

  function copyEmailInviteLink(token) {
    navigator.clipboard.writeText(`${window.location.origin}/invite/${token}`)
    toast.success('Invite link copied')
  }

  return (
    <>
      <Modal open={open} onClose={onClose} title="Share Project" className="max-w-xl">
        <div className="space-y-6">
          {isOwner && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Anyone with this link can join this project.
              </p>
              <InviteLinkCard
                projectId={project.id}
                linkInvitation={linkInvitation}
                linkEverExisted={linkEverExisted}
                isLoading={invitationsLoading}
              />

              <div>
                <p className="mb-2 text-xs font-semibold tracking-wide text-gray-500">
                  OPTIONAL — INVITE BY EMAIL
                </p>
                <InviteByEmailForm projectId={project.id} />
                <p className="mt-2 text-xs text-muted-foreground">
                  Email invitations are optional. The invite link above is the primary way to
                  share this project.
                </p>
              </div>
            </div>
          )}

          <div>
            <p className="mb-1 text-xs font-semibold tracking-wide text-gray-500">
              PEOPLE WITH ACCESS
            </p>
            <div className="divide-y divide-border">
              <AccessRow
                name={project.owner_name}
                email={project.owner_email}
                badge="Owner"
                badgeVariant="purple"
                menu={
                  isOwner && (
                    <DropdownMenu
                      trigger={(triggerProps) => (
                        <button
                          type="button"
                          aria-label="Owner actions"
                          className="rounded-md p-1 text-gray-400 hover:bg-muted hover:text-gray-700"
                          {...triggerProps}
                        >
                          <MoreVertical className="size-4" />
                        </button>
                      )}
                    >
                      <DropdownMenuItem
                        icon={ArrowRightLeft}
                        onClick={() =>
                          toast.info("Transfer ownership before leaving. This isn't available yet.")
                        }
                      >
                        Transfer ownership before leaving
                      </DropdownMenuItem>
                    </DropdownMenu>
                  )
                }
              />

              {membersLoading && (
                <p className="py-3 text-sm text-muted-foreground">Loading collaborators...</p>
              )}

              {members?.map((member) => (
                <AccessRow
                  key={member.user_id}
                  name={member.name}
                  email={member.email}
                  badge="Accepted"
                  badgeVariant="success"
                  menu={
                    isOwner && (
                      <DropdownMenu
                        trigger={(triggerProps) => (
                          <button
                            type="button"
                            aria-label={`Actions for ${member.name}`}
                            className="rounded-md p-1 text-gray-400 hover:bg-muted hover:text-gray-700"
                            {...triggerProps}
                          >
                            <MoreVertical className="size-4" />
                          </button>
                        )}
                      >
                        <DropdownMenuItem
                          icon={UserX}
                          destructive
                          onClick={() => setRemovingMember(member)}
                        >
                          Remove from project
                        </DropdownMenuItem>
                      </DropdownMenu>
                    )
                  }
                />
              ))}

              {pendingEmailInvitations.map((invitation) => (
                <AccessRow
                  key={invitation.id}
                  name={null}
                  email={invitation.email}
                  badge="Pending"
                  badgeVariant="warning"
                  menu={
                    <DropdownMenu
                      trigger={(triggerProps) => (
                        <button
                          type="button"
                          aria-label={`Actions for ${invitation.email}`}
                          className="rounded-md p-1 text-gray-400 hover:bg-muted hover:text-gray-700"
                          {...triggerProps}
                        >
                          <MoreVertical className="size-4" />
                        </button>
                      )}
                    >
                      <DropdownMenuItem
                        icon={X}
                        destructive
                        onClick={() => setCancellingInvitation(invitation)}
                      >
                        Cancel Invitation
                      </DropdownMenuItem>
                    </DropdownMenu>
                  }
                />
              ))}

              {!membersLoading &&
                members?.length === 0 &&
                pendingEmailInvitations.length === 0 && (
                  <p className="py-3 text-sm text-muted-foreground">
                    No collaborators yet. Share the invite link above to add people.
                  </p>
                )}
            </div>
          </div>

          {isOwner && (invitationsLoading || pendingEmailInvitations.length > 0) && (
            <div>
              <p className="mb-1 text-xs font-semibold tracking-wide text-gray-500">
                PENDING INVITATIONS
              </p>
              {invitationsLoading && (
                <p className="py-2 text-sm text-muted-foreground">Loading invitations...</p>
              )}
              <div className="space-y-2">
                {pendingEmailInvitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    data-testid="pending-invitation-row"
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border px-4 py-2.5"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">{invitation.email}</p>
                      <div className="mt-0.5 flex items-center gap-2">
                        <Badge variant="warning">Pending</Badge>
                        <span className="text-xs text-muted-foreground">
                          Sent {formatRelative(invitation.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => resendInvitation.mutate(invitation.id)}
                        disabled={resendInvitation.isPending}
                      >
                        <RotateCw className="size-3.5" />
                        Resend
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => copyEmailInviteLink(invitation.token)}
                      >
                        <Copy className="size-3.5" />
                        Copy Link
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => setCancellingInvitation(invitation)}
                      >
                        <X className="size-3.5" />
                        Cancel
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end border-t border-border pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={Boolean(removingMember)}
        onClose={() => setRemovingMember(null)}
        onConfirm={handleConfirmRemove}
        title="Remove collaborator"
        description={`Remove ${removingMember?.name ?? 'this person'} from "${project.name}"? They'll lose access immediately.`}
        confirmLabel="Remove"
        destructive
        isConfirming={removeMember.isPending}
      />

      <ConfirmDialog
        open={Boolean(cancellingInvitation)}
        onClose={() => setCancellingInvitation(null)}
        onConfirm={handleConfirmCancel}
        title="Cancel invitation"
        description={`Cancel the pending invitation to ${cancellingInvitation?.email ?? ''}?`}
        confirmLabel="Cancel invitation"
        destructive
        isConfirming={revokeInvitation.isPending}
      />
    </>
  )
}

export { ShareModal }
