import { useAuth } from '@/app/providers/AuthProvider'
import { useProjectMembers, useRemoveProjectMember } from '../hooks/useProjectMembers'
import { TeamMemberChip } from './TeamMemberChip'

function TeamMembersSection({ projectId, ownerId }) {
  const { user } = useAuth()
  const { data: members, isLoading } = useProjectMembers(projectId)
  const removeMember = useRemoveProjectMember(projectId)
  const isOwner = user?.id === ownerId

  return (
    <div>
      {isLoading && <span className="text-sm text-muted-foreground">Loading team...</span>}
      {members?.length === 0 && !isLoading && (
        <span className="text-sm text-muted-foreground">
          No collaborators yet. Invite your team from Project Settings.
        </span>
      )}
      <div className="flex flex-wrap gap-2">
        {members?.map((member, i) => (
          <TeamMemberChip
            key={member.user_id}
            name={member.name}
            color={i % 2 === 0 ? 'blue' : 'navy'}
            onRemove={isOwner ? () => removeMember.mutate(member.user_id) : undefined}
          />
        ))}
      </div>
    </div>
  )
}

export { TeamMembersSection }
