import { useState } from 'react'
import { User } from 'lucide-react'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { useAuth } from '@/app/providers/AuthProvider'
import { getApiErrorMessage } from '@/shared/lib/apiError'

function InviteOnboardingForm({ token, projectName, inviterName, onJoined }) {
  const { onboard } = useAuth()
  const [name, setName] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    const value = name.trim()
    if (!value || submitting) return
    setError(null)
    setSubmitting(true)
    try {
      const data = await onboard(token, value)
      onJoined(data.project_id)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not join the project. Please try again.'))
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="mb-1 text-xl font-bold text-gray-900">Join {projectName}</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        {inviterName} invited you to collaborate on this project.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
            FULL NAME
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

        <Button type="submit" size="lg" className="w-full" disabled={!name.trim() || submitting}>
          {submitting ? 'Joining...' : 'Join Project'}
        </Button>
      </form>
    </div>
  )
}

export { InviteOnboardingForm }
