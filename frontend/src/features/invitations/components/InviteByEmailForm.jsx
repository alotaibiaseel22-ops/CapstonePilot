import { useState } from 'react'
import { Mail, X } from 'lucide-react'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { useInviteByEmail } from '../hooks/useInvitations'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function InviteByEmailForm({ projectId }) {
  const inviteByEmail = useInviteByEmail(projectId)
  const [emails, setEmails] = useState([])
  const [input, setInput] = useState('')
  const [error, setError] = useState(null)
  const [sent, setSent] = useState(false)

  function addEmail(e) {
    if (e.key !== 'Enter' && e.key !== ',') return
    e.preventDefault()
    const value = input.trim().replace(/,$/, '')
    if (!value) return
    if (!EMAIL_PATTERN.test(value)) {
      setError(`"${value}" doesn't look like a valid email.`)
      return
    }
    if (emails.includes(value)) {
      setInput('')
      return
    }
    setEmails((prev) => [...prev, value])
    setInput('')
    setError(null)
  }

  function removeEmail(email) {
    setEmails((prev) => prev.filter((e) => e !== email))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (emails.length === 0 || inviteByEmail.isPending) return
    setError(null)
    setSent(false)
    try {
      await inviteByEmail.mutateAsync(emails)
      setEmails([])
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Could not send one or more invitations.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Input
        icon={Mail}
        placeholder="Enter an email and press Enter..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={addEmail}
      />

      {emails.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {emails.map((email) => (
            <span
              key={email}
              className="inline-flex items-center gap-2 rounded-full bg-blue-50 py-1 pl-3 pr-2 text-sm font-medium text-blue-700"
            >
              {email}
              <button type="button" onClick={() => removeEmail(email)} aria-label={`Remove ${email}`}>
                <X className="size-3.5 text-blue-400 hover:text-blue-600" />
              </button>
            </span>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
      {sent && <p className="text-sm text-green-600">Invitations sent.</p>}

      <Button type="submit" size="sm" disabled={emails.length === 0 || inviteByEmail.isPending}>
        {inviteByEmail.isPending
          ? 'Sending...'
          : emails.length === 1
            ? 'Send Invitation'
            : 'Send Invitations'}
      </Button>
    </form>
  )
}

export { InviteByEmailForm }
