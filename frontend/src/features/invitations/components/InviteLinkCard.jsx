import { useState } from 'react'
import { Link2, Copy, Check } from 'lucide-react'
import { Button } from '@/shared/components/ui/button'
import { useLinkInvitation } from '../hooks/useInvitations'

function InviteLinkCard({ projectId }) {
  const linkInvitation = useLinkInvitation(projectId)
  const [copied, setCopied] = useState(false)

  async function handleClick() {
    const invitation = await linkInvitation.mutateAsync()
    const url = `${window.location.origin}/invite/${invitation.token}`
    await navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-border p-4">
      <div className="flex items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
          <Link2 className="size-4" />
        </span>
        <div>
          <p className="text-sm font-semibold text-gray-900">Shareable invite link</p>
          <p className="text-xs text-muted-foreground">
            Anyone with this link can join as a Collaborator after signing in.
          </p>
        </div>
      </div>
      <Button type="button" variant="outline" size="sm" onClick={handleClick} disabled={linkInvitation.isPending}>
        {copied ? <Check className="size-4 text-green-600" /> : <Copy className="size-4" />}
        {copied ? 'Copied' : 'Copy link'}
      </Button>
    </div>
  )
}

export { InviteLinkCard }
