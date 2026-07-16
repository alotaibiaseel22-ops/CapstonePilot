import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Ban, Check, Copy, Link2, MoreVertical, RotateCw } from 'lucide-react'
import { Button } from '@/shared/components/ui/button'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'
import { getOrCreateLinkInvitation } from '../api/invitations'
import {
  useLinkInvitation,
  useRegenerateLinkInvitation,
  useDisableLinkInvitation,
} from '../hooks/useInvitations'

function InviteLinkSection({ projectId, linkInvitation, linkEverExisted, isLoading }) {
  const queryClient = useQueryClient()
  const ensureLink = useLinkInvitation(projectId)
  const regenerateLink = useRegenerateLinkInvitation(projectId)
  const disableLink = useDisableLinkInvitation(projectId)
  const [copied, setCopied] = useState(false)
  const [autoCreating, setAutoCreating] = useState(false)
  const autoCreateFiredRef = useRef(false)

  // The link is meant to already be there the moment the modal opens (it's
  // the primary share method), not appear only after a first click - but
  // only the first time. Once the owner explicitly disables it (so a link
  // invitation exists in a revoked state), silently recreating it here
  // would defeat the point of disabling; that requires the explicit
  // "Create New Link" button instead. The ref (set synchronously) is what
  // prevents a double-fire under StrictMode's dev-mode double-invoke of
  // effects.
  //
  // This deliberately calls the API function directly instead of going
  // through useLinkInvitation()'s mutate(): a mutation fired from a mount
  // effect can have its observer detached by StrictMode's phantom unmount
  // before it settles, which left both mutation.isPending AND a per-call
  // onSettled callback stuck/never-firing in practice, even though the
  // request itself succeeded. A plain promise with try/finally has no
  // observer to detach, so it can't get stuck.
  useEffect(() => {
    if (isLoading || linkInvitation || linkEverExisted || autoCreateFiredRef.current) return
    autoCreateFiredRef.current = true
    setAutoCreating(true)
    getOrCreateLinkInvitation(projectId)
      .then(() => {
        queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] })
      })
      .catch((error) => {
        toast.error(error.response?.data?.detail ?? 'Something went wrong. Could not load the invite link.')
      })
      .finally(() => setAutoCreating(false))
  }, [isLoading, linkInvitation, linkEverExisted, projectId, queryClient])

  async function copyLink(token) {
    await navigator.clipboard.writeText(`${window.location.origin}/invite/${token}`)
    setCopied(true)
    toast.success('Invite link copied')
    setTimeout(() => setCopied(false), 2000)
  }

  const preparing = isLoading || (!linkInvitation && autoCreating)
  const disabled = !preparing && !linkInvitation

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Invite Link</h3>
        <p className="text-sm text-muted-foreground">
          Anyone with this secure link can join this project.
        </p>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex h-11 min-w-0 flex-1 items-center gap-2 rounded-lg border border-border bg-gray-50 px-3.5">
          <Link2 className="size-4 shrink-0 text-gray-400" />
          <span className="truncate text-sm text-gray-500">
            {linkInvitation ? (
              <span className="font-mono tracking-widest">••••••••••••••••••</span>
            ) : disabled ? (
              'Link sharing is currently disabled for this project.'
            ) : (
              'Preparing your invite link...'
            )}
          </span>
        </div>

        {linkInvitation ? (
          <>
            <Button type="button" onClick={() => copyLink(linkInvitation.token)}>
              {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
              {copied ? 'Copied' : 'Copy Link'}
            </Button>
            <DropdownMenu
              trigger={(triggerProps) => (
                <button
                  type="button"
                  aria-label="Invite link options"
                  className="flex h-11 w-10 shrink-0 items-center justify-center rounded-lg border border-border text-gray-500 hover:bg-muted hover:text-gray-700"
                  {...triggerProps}
                >
                  <MoreVertical className="size-4" />
                </button>
              )}
            >
              <DropdownMenuItem
                icon={RotateCw}
                onClick={() => regenerateLink.mutate()}
                disabled={regenerateLink.isPending}
              >
                Regenerate Link
              </DropdownMenuItem>
              <DropdownMenuItem
                icon={Ban}
                destructive
                onClick={() => disableLink.mutate(linkInvitation.id)}
                disabled={disableLink.isPending}
              >
                Disable Link
              </DropdownMenuItem>
            </DropdownMenu>
          </>
        ) : (
          <Button
            type="button"
            onClick={() => ensureLink.mutate()}
            disabled={!disabled || ensureLink.isPending}
          >
            <Link2 className="size-4" />
            Create New Link
          </Button>
        )}
      </div>
    </div>
  )
}

export { InviteLinkSection }
