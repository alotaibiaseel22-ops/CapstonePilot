import { useState } from 'react'
import { Mail } from 'lucide-react'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { useInviteByEmail } from '../hooks/useInvitations'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function InviteByEmailForm({ projectId }) {
  const inviteByEmail = useInviteByEmail(projectId)
  const [email, setEmail] = useState('')
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const value = email.trim()
    if (!value || inviteByEmail.isPending) return
    if (!EMAIL_PATTERN.test(value)) {
      setError(`"${value}" doesn't look like a valid email.`)
      return
    }
    setError(null)
    try {
      await inviteByEmail.mutateAsync([value])
      setEmail('')
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Could not send the invitation.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="flex items-center gap-2">
        <Input
          icon={Mail}
          type="email"
          placeholder="name@example.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            if (error) setError(null)
          }}
          className="flex-1"
        />
        <Button type="submit" variant="outline" disabled={!email.trim() || inviteByEmail.isPending}>
          {inviteByEmail.isPending ? 'Inviting...' : 'Invite'}
        </Button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  )
}

export { InviteByEmailForm }
