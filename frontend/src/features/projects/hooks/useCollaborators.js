import { useProject } from './useProjects'
import { useProjectMembers } from './useProjectMembers'
import { useProjectGuests } from './useProjectGuests'

// The single place that combines the three genuinely separate data sources
// (project.owner, real ProjectMembers, Guests) into one "collaborators"
// list. No such combined view existed before this - the owner is a
// projects.owner_id FK (never a project_members row), members and guests
// live in two different tables with two different id spaces, and nothing
// previously fetched all three together. Deduplicated by `id` (never by
// `name`/`display_name` - two different guests can legitimately share a
// display name, e.g. two separate people both named "Sara" who joined via
// two different browsers/devices, and must never collapse into one row).
function useCollaborators(projectId) {
  const { data: project, isLoading: projectLoading, isError: projectError } = useProject(projectId)
  const { data: members, isLoading: membersLoading, isError: membersError } =
    useProjectMembers(projectId)
  const { data: guests, isLoading: guestsLoading, isError: guestsError } =
    useProjectGuests(projectId)

  const isLoading = projectLoading || membersLoading || guestsLoading
  const isError = projectError || membersError || guestsError

  if (isLoading || isError || !project) {
    return { collaborators: [], isLoading, isError }
  }

  const byId = new Map()

  byId.set(project.owner_id, {
    id: project.owner_id,
    name: project.owner_name,
    email: project.owner_email,
    role: 'owner',
  })

  for (const member of members ?? []) {
    // A defensive guard, not a real-world case today (list_members never
    // returns the owner) - but if it ever did, the owner entry above must
    // win rather than being silently overwritten by a "Member" one.
    if (!byId.has(member.user_id)) {
      byId.set(member.user_id, {
        id: member.user_id,
        name: member.name,
        email: member.email,
        role: 'member',
      })
    }
  }

  for (const guest of guests ?? []) {
    if (!byId.has(guest.id)) {
      byId.set(guest.id, {
        id: guest.id,
        name: guest.display_name,
        email: null,
        role: 'guest',
      })
    }
  }

  return { collaborators: Array.from(byId.values()), isLoading: false, isError: false }
}

export { useCollaborators }
