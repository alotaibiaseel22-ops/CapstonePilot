import { useState } from 'react'
import { Users } from 'lucide-react'
import { Input } from '@/shared/components/ui/input'
import { useProjectMembers, useAddProjectMember, useRemoveProjectMember } from '../hooks/useProjectMembers'
import { TeamMemberChip } from './TeamMemberChip'

function TeamMembersSection({ projectId }) {
  const { data: members, isLoading } = useProjectMembers(projectId)
  const addMember = useAddProjectMember(projectId)
  const removeMember = useRemoveProjectMember(projectId)
  const [email, setEmail] = useState('')
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!email.trim()) return
    setError(null)
    try {
      await addMember.mutateAsync(email.trim())
      setEmail('')
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Could not add that team member.')
    }
  }

  return (
    <div>
      <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">TEAM MEMBERS</label>
      <form onSubmit={handleSubmit}>
        <Input
          icon={Users}
          type="email"
          placeholder="Add team member by email..."
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={addMember.isPending}
        />
      </form>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}

      <div className="mt-3 flex flex-wrap gap-2">
        {isLoading && <span className="text-sm text-muted-foreground">Loading team...</span>}
        {members?.length === 0 && !isLoading && (
          <span className="text-sm text-muted-foreground">No team members yet.</span>
        )}
        {members?.map((member, i) => (
          <TeamMemberChip
            key={member.user_id}
            name={member.name}
            color={i % 2 === 0 ? 'blue' : 'navy'}
            onRemove={() => removeMember.mutate(member.user_id)}
          />
        ))}
      </div>
    </div>
  )
}

export { TeamMembersSection }
