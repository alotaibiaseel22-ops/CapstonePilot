import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Link2, Copy, Check, RotateCw, Ban } from 'lucide-react'
import { Button } from '@/shared/components/ui/button'
import { getOrCreateLinkInvitation } from '../api/invitations'
import {
  useLinkInvitation,
  useRegenerateLinkInvitation,
  useDisableLinkInvitation,
} from '../hooks/useInvitations'

function InviteLinkCard({ projectId, linkInvitation, linkEverExisted, isLoading }) {
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
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
          <Link2 className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-gray-900">Anyone with this link can join</p>
          <p className="truncate text-xs text-muted-foreground">
            {linkInvitation
              ? `${window.location.origin}/invite/${linkInvitation.token}`
              : disabled
                ? 'Link sharing is currently disabled for this project.'
                : 'Preparing your invite link...'}
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {linkInvitation ? (
          <>
            <Button type="button" size="sm" onClick={() => copyLink(linkInvitation.token)}>
              {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
              {copied ? 'Copied' : 'Copy Invite Link'}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => regenerateLink.mutate()}
              disabled={regenerateLink.isPending}
            >
              <RotateCw className="size-3.5" />
              Regenerate Link
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="text-red-600 hover:bg-red-50"
              onClick={() => disableLink.mutate(linkInvitation.id)}
              disabled={disableLink.isPending}
            >
              <Ban className="size-3.5" />
              Disable Link
            </Button>
          </>
        ) : (
          <Button
            type="button"
            size="sm"
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

export { InviteLinkCard }
