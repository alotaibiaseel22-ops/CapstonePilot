import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Button } from '@/shared/components/ui/button'
import { useAuth } from '@/app/providers/AuthProvider'
import { acceptInvitation, getInvitationPreview } from '../api/invitations'

function InviteAcceptPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { status } = useAuth()
  const [error, setError] = useState(null)
  const hasAccepted = useRef(false)
  const hasRedirected = useRef(false)

  useEffect(() => {
    if (status !== 'authenticated' || hasAccepted.current) return
    hasAccepted.current = true

    acceptInvitation(token)
      .then((result) => {
        toast.success('You joined the project')
        navigate(`/projects/${result.project_id}`, { replace: true })
      })
      .catch((err) => {
        setError(err.response?.data?.detail ?? 'This invitation link is invalid or has expired.')
      })
  }, [status, token, navigate])

  useEffect(() => {
    if (status !== 'unauthenticated' || hasRedirected.current) return
    hasRedirected.current = true

    getInvitationPreview(token)
      .then((preview) => {
        // A known email invite for someone without an account skips the
        // login detour and goes straight to Sign Up, prefilled. Everything
        // else (existing accounts, shareable links with no known email)
        // goes to Login, which itself links through to Sign Up.
        const destination = preview.email && !preview.user_exists ? '/register' : '/login'
        navigate(destination, {
          replace: true,
          state: { from: `/invite/${token}`, inviteEmail: preview.email ?? undefined },
        })
      })
      .catch(() => {
        navigate('/login', { replace: true, state: { from: `/invite/${token}` } })
      })
  }, [status, token, navigate])

  if (error) {
    return (
      <div className="mx-auto max-w-md space-y-4 py-16">
        <ErrorState message={error} />
        <Link to="/dashboard">
          <Button type="button" variant="outline" className="w-full">
            Go to Dashboard
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-3 py-16">
      <CheckCircle2 className="size-8 text-blue-500" />
      <LoadingState label={status === 'authenticated' ? 'Joining project...' : 'Checking your invitation...'} />
    </div>
  )
}

export { InviteAcceptPage }
