import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { CheckCircle2, Cpu } from 'lucide-react'
import { toast } from 'sonner'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { useAuth } from '@/app/providers/AuthProvider'
import { acceptInvitation, getInvitationPreview } from '../api/invitations'
import { InviteOnboardingForm } from '../components/InviteOnboardingForm'

function InviteAcceptPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { status } = useAuth()
  const [error, setError] = useState(null)
  const [onboardingPreview, setOnboardingPreview] = useState(null)
  const hasAccepted = useRef(false)
  const hasCheckedPreview = useRef(false)

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
    if (status !== 'unauthenticated' || hasCheckedPreview.current) return
    hasCheckedPreview.current = true

    getInvitationPreview(token)
      .then((preview) => {
        // A valid email invite for someone without an account yet skips
        // Login/Register entirely and joins with just a name - the token
        // already proves who they are. Everything else (an email that
        // already has an account, or a shareable link with no specific
        // invited email) falls back to the normal Login/Register detour,
        // exactly as before: an invitation link must never double as a
        // password-less login for an existing account.
        if (preview.is_valid && preview.email && !preview.user_exists) {
          setOnboardingPreview(preview)
          return
        }
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

  function handleJoined(projectId) {
    toast.success('You joined the project')
    navigate(`/projects/${projectId}`, { replace: true })
  }

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

  if (onboardingPreview) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
        <div className="w-full max-w-sm">
          <div className="mb-6 flex items-center justify-center gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-600">
              <Cpu className="size-5 text-white" />
            </span>
            <div>
              <p className="text-base font-bold leading-tight text-gray-900">CapstonePilot</p>
              <p className="text-xs text-muted-foreground">AI Platform</p>
            </div>
          </div>
          <Card>
            <CardContent>
              <InviteOnboardingForm
                token={token}
                projectName={onboardingPreview.project_name}
                inviterName={onboardingPreview.inviter_name}
                onJoined={handleJoined}
              />
            </CardContent>
          </Card>
        </div>
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
