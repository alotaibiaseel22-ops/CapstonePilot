import { useParams, Link } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProject } from '@/features/projects/hooks/useProjects'
import { useProjectMembers } from '@/features/projects/hooks/useProjectMembers'
import { useProjectGuests } from '@/features/projects/hooks/useProjectGuests'
import { getTasks } from '../api/milestones'
import { useMilestones } from '../hooks/useMilestones'
import { MilestoneAccordion } from '../components/MilestoneAccordion'
import { PlanApprovalBanner } from '../components/PlanApprovalBanner'

function ProgressPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const { data: project, isLoading: projectLoading, isError: projectError } = useProject(id)
  const { data: milestones, isLoading: milestonesLoading, isError: milestonesError } = useMilestones(id)
  const { data: projectMembers = [] } = useProjectMembers(id)
  const { data: guests = [] } = useProjectGuests(id)

  // list_members never includes the project owner, but the owner is a
  // perfectly valid assignee too - prepended here rather than changing what
  // that endpoint returns (ShareModal.jsx already renders the owner
  // separately from `members` for the same reason). `role: 'owner'` here is
  // a synthetic display-only marker - list_members' own `role` field means
  // something different (a user's account-wide role), but the two never
  // collide since a real API row's role is always 'project_owner'/'collaborator'.
  const assignableMembers = project
    ? [
        { user_id: project.owner_id, name: project.owner_name, role: 'owner' },
        ...projectMembers,
      ]
    : []

  const taskQueries = useQueries({
    queries: (milestones ?? []).map((m) => ({
      queryKey: ['milestones', m.id, 'tasks'],
      queryFn: () => getTasks(m.id),
      enabled: Boolean(milestones),
    })),
  })

  const isLoading = projectLoading || milestonesLoading
  const isError = projectError || milestonesError

  if (isLoading) return <LoadingState label="Loading project plan..." />
  if (isError) return <ErrorState message="Couldn't load the project plan. Please try again." />

  const allTasks = taskQueries.flatMap((q) => q.data ?? [])
  const totalTasks = allTasks.length
  const doneTasks = allTasks.filter((t) => t.status === 'done').length
  const overallPercent = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0

  return (
    <div className="space-y-6">
      <Link to={`/projects/${id}`} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-gray-700">
        <ArrowLeft className="size-4" />
        Back to project
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Project Plan</h1>
          <p className="mt-1 text-muted-foreground">
            {project.name} &middot; {milestones.length} milestone{milestones.length === 1 ? '' : 's'} &middot;{' '}
            {totalTasks} task{totalTasks === 1 ? '' : 's'}
          </p>
        </div>
        <span className="rounded-full border border-border bg-white px-4 py-2 text-sm">
          Overall <span className="font-bold text-blue-600">{overallPercent}%</span>
        </span>
      </div>

      <PlanApprovalBanner projectId={id} isOwner={user?.id === project.owner_id} />

      {milestones.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center text-muted-foreground">
          No milestones yet for this project.
        </div>
      ) : (
        <div className="space-y-4">
          {milestones.map((milestone) => (
            <MilestoneAccordion
              key={milestone.id}
              milestone={milestone}
              members={assignableMembers}
              guests={guests}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export { ProgressPage }
