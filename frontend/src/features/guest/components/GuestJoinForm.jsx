import { useEffect, useState } from 'react'
import { User } from 'lucide-react'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { Card, CardContent } from '@/shared/components/ui/card'
import { useGuestSession } from '@/app/providers/GuestSessionProvider'
import { getInvitationPreview } from '@/features/invitations/api/invitations'
import { getApiErrorMessage } from '@/shared/lib/apiError'

function GuestJoinForm() {
  const { invitationToken, join } = useGuestSession()
  const [preview, setPreview] = useState(null)
  const [name, setName] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    getInvitationPreview(invitationToken)
      .then((data) => {
        if (!cancelled) setPreview(data)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [invitationToken])

  async function handleSubmit(e) {
    e.preventDefault()
    const value = name.trim()
    if (!value || submitting) return
    setError(null)
    setSubmitting(true)
    try {
      await join(value)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not join the project. Please try again.'))
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-sm">
        <Card>
          <CardContent>
            <h1 className="mb-1 text-xl font-bold text-gray-900">
              Join {preview?.project_name ?? 'this project'}
            </h1>
            <p className="mb-6 text-sm text-muted-foreground">
              {preview?.inviter_name ?? 'Someone'} shared this project with you. No account
              needed - just enter a name to continue.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                  YOUR NAME
                </label>
                <Input
                  icon={User}
                  required
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                />
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={!name.trim() || submitting}
              >
                {submitting ? 'Joining...' : 'Continue'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export { GuestJoinForm }
