import { useState } from 'react'
import { toast } from 'sonner'
import { Copy, MoreVertical, RotateCw, User, UserX, X } from 'lucide-react'
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
import { InviteLinkSection } from '@/features/invitations/components/InviteLinkSection'
import { ProfileModal } from './ProfileModal'

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

function copyEmail(email) {
  navigator.clipboard.writeText(email)
  toast.success('Email copied')
}

function RowMenu({ label, children }) {
  return (
    <DropdownMenu
      trigger={(triggerProps) => (
        <button
          type="button"
          aria-label={label}
          className="rounded-md p-1 text-gray-400 hover:bg-white hover:text-gray-700"
          {...triggerProps}
        >
          <MoreVertical className="size-4" />
        </button>
      )}
    >
      {children}
    </DropdownMenu>
  )
}

function AccessRow({ name, email, isYou, badge, badgeVariant, menu }) {
  return (
    <div
      data-testid="access-row"
      className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted"
    >
      <div className="flex min-w-0 items-center gap-3">
        <Avatar initials={initialsOf(name || email)} className="shrink-0" />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-900">
            {name || email}
            {isYou && <span className="font-normal text-muted-foreground"> (You)</span>}
          </p>
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
  const [viewingProfile, setViewingProfile] = useState(null)

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
    try {
      await removeMember.mutateAsync(removingMember.user_id)
      setRemovingMember(null)
    } catch {
      // Error toast is already shown by the mutation's onError; leave the
      // dialog open so the owner can see it and retry or cancel.
    }
  }

  async function handleConfirmCancel() {
    try {
      await revokeInvitation.mutateAsync(cancellingInvitation.id)
      setCancellingInvitation(null)
    } catch {
      // Error toast is already shown by the mutation's onError; leave the
      // dialog open so the owner can see it and retry or cancel.
    }
  }

  function copyEmailInviteLink(token) {
    navigator.clipboard.writeText(`${window.location.origin}/invite/${token}`)
    toast.success('Invite link copied')
  }

  return (
    <>
      <Modal
        open={open}
        onClose={onClose}
        title="Share Project"
        description="Invite teammates or share a secure link to collaborate."
        className="max-w-xl"
      >
        <div className="space-y-6">
          {isOwner && (
            <>
              <InviteLinkSection
                projectId={project.id}
                linkInvitation={linkInvitation}
                linkEverExisted={linkEverExisted}
                isLoading={invitationsLoading}
              />

              <div className="border-t border-border pt-6">
                <h3 className="mb-2 text-sm font-semibold text-gray-900">
                  Invite by Email <span className="font-normal text-muted-foreground">(Optional)</span>
                </h3>
                <InviteByEmailForm projectId={project.id} />
              </div>
            </>
          )}

          <div className={isOwner ? 'border-t border-border pt-6' : ''}>
            <h3 className="mb-2 text-sm font-semibold text-gray-900">People with Access</h3>
            <div className="divide-y divide-border">
              <AccessRow
                name={project.owner_name}
                email={project.owner_email}
                isYou={isOwner}
                badge="Owner"
                badgeVariant="purple"
                menu={
                  <RowMenu label="Owner actions">
                    <DropdownMenuItem icon={Copy} onClick={() => copyEmail(project.owner_email)}>
                      Copy Email
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      icon={User}
                      onClick={() =>
                        setViewingProfile({
                          name: project.owner_name,
                          email: project.owner_email,
                          badge: 'Owner',
                          badgeVariant: 'purple',
                        })
                      }
                    >
                      View Profile
                    </DropdownMenuItem>
                  </RowMenu>
                }
              />

              {membersLoading && (
                <p className="py-3 text-sm text-muted-foreground">Loading collaborators...</p>
              )}

              {members?.map((member) => {
                const isYou = member.user_id === user?.id
                return (
                  <AccessRow
                    key={member.user_id}
                    name={member.name}
                    email={member.email}
                    isYou={isYou}
                    badge="Member"
                    badgeVariant="success"
                    menu={
                      <RowMenu label={`Actions for ${member.name}`}>
                        {isOwner && !isYou && (
                          <DropdownMenuItem
                            icon={UserX}
                            destructive
                            onClick={() => setRemovingMember(member)}
                          >
                            Remove from Project
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem icon={Copy} onClick={() => copyEmail(member.email)}>
                          Copy Email
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          icon={User}
                          onClick={() =>
                            setViewingProfile({
                              name: member.name,
                              email: member.email,
                              badge: 'Member',
                              badgeVariant: 'success',
                              joinedAt: member.added_at,
                            })
                          }
                        >
                          View Profile
                        </DropdownMenuItem>
                      </RowMenu>
                    }
                  />
                )
              })}
            </div>

            {!membersLoading && members?.length === 0 && (
              <p className="mt-3 text-sm text-muted-foreground">
                Only you have access to this project. Share the invite link to start
                collaborating.
              </p>
            )}
          </div>

          {isOwner && (invitationsLoading || pendingEmailInvitations.length > 0) && (
            <div className="border-t border-border pt-6">
              <h3 className="mb-2 text-sm font-semibold text-gray-900">Pending Invitations</h3>
              {invitationsLoading && (
                <p className="py-2 text-sm text-muted-foreground">Loading invitations...</p>
              )}
              <div className="divide-y divide-border">
                {pendingEmailInvitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    data-testid="pending-invitation-row"
                    className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-gray-900">
                        {invitation.email}
                      </p>
                      <div className="mt-0.5 flex items-center gap-2">
                        <Badge variant="warning">Pending</Badge>
                        <span className="text-xs text-muted-foreground">
                          Sent {formatRelative(invitation.created_at)}
                        </span>
                      </div>
                    </div>
                    <RowMenu label={`Actions for ${invitation.email}`}>
                      <DropdownMenuItem
                        icon={RotateCw}
                        onClick={() => resendInvitation.mutate(invitation.id)}
                        disabled={resendInvitation.isPending}
                      >
                        Resend Invitation
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        icon={Copy}
                        onClick={() => copyEmailInviteLink(invitation.token)}
                      >
                        Copy Invite Link
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        icon={X}
                        destructive
                        onClick={() => setCancellingInvitation(invitation)}
                      >
                        Cancel Invitation
                      </DropdownMenuItem>
                    </RowMenu>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end border-t border-border pt-5">
            <Button type="button" variant="ghost" onClick={onClose}>
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

      <ProfileModal profile={viewingProfile} onClose={() => setViewingProfile(null)} />
    </>
  )
}

export { ShareModal }
