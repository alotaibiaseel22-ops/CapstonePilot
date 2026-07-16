import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Cpu, Mail, Lock, User } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { useAuth } from '@/app/providers/AuthProvider'

function RegisterPage() {
  const { status, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const cameFromInvite = Boolean(location.state?.from?.startsWith('/invite/'))
  // No role picker in the UI: arriving via an invite link always means
  // joining as a Collaborator; registering directly always means starting
  // your own project as a Project Owner. You can still be invited as a
  // Collaborator on other projects later regardless of this default.
  const role = cameFromInvite ? 'collaborator' : 'project_owner'

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated') {
    return <Navigate to={location.state?.from ?? '/dashboard'} replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register({ name, email, password, role })
      navigate(location.state?.from ?? '/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Could not create your account. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

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
            <h1 className="mb-1 text-xl font-bold text-gray-900">Create your account</h1>
            <p className="mb-6 text-sm text-muted-foreground">
              {cameFromInvite
                ? "You're joining a project as a Collaborator."
                : 'Start managing your capstone project with AI.'}
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">NAME</label>
                <Input icon={User} required value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">EMAIL</label>
                <Input
                  icon={Mail}
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">PASSWORD</label>
                <Input
                  icon={Lock}
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button type="submit" size="lg" className="w-full" disabled={submitting}>
                {submitting ? 'Creating account...' : 'Create account'}
              </Button>
            </form>

            <p className="mt-4 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" state={location.state} className="font-medium text-blue-600 hover:underline">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export { RegisterPage }
