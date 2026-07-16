import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Button } from '@/shared/components/ui/button'
import { acceptInvitation } from '../api/invitations'

function InviteAcceptPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const [error, setError] = useState(null)
  const hasRun = useRef(false)

  useEffect(() => {
    if (hasRun.current) return
    hasRun.current = true

    acceptInvitation(token)
      .then((result) => {
        navigate(`/projects/${result.project_id}`, { replace: true })
      })
      .catch((err) => {
        setError(err.response?.data?.detail ?? 'This invitation link is invalid or has expired.')
      })
  }, [token, navigate])

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
      <LoadingState label="Joining project..." />
    </div>
  )
}

export { InviteAcceptPage }
