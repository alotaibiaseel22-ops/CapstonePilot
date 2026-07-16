import { useParams, Link } from 'react-router-dom'
import { Users, CalendarClock, Flag, ClipboardList } from 'lucide-react'
import { StatCard } from '@/shared/components/common/StatCard'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { useProject } from '../hooks/useProjects'
import { useProjectMembers } from '../hooks/useProjectMembers'
import { useMilestones } from '@/features/planning/hooks/useMilestones'
import { TeamMembersSection } from '../components/TeamMembersSection'

const statusTone = { planning: 'default', active: 'info', completed: 'success' }
const statusLabel = { planning: 'Planning', active: 'Active', completed: 'Completed' }

function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project, isLoading, isError } = useProject(id)
  const { data: members } = useProjectMembers(id)
  const { data: milestones } = useMilestones(id)

  if (isLoading) return <LoadingState label="Loading project..." />

  if (isError || !project) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Project not found</h1>
        <ErrorState message="This project doesn't exist or may have been removed." />
        <Link to="/projects">
          <Button type="button" variant="outline">
            Back to Projects
          </Button>
        </Link>
      </div>
    )
  }

  const daysRemaining = project.due_date
    ? Math.ceil((new Date(project.due_date) - new Date()) / (1000 * 60 * 60 * 24))
    : null

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <Badge variant={statusTone[project.status]}>{statusLabel[project.status] ?? project.status}</Badge>
        </div>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          {project.description || 'No description provided.'}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} tone="purple" value={members?.length ?? '—'} label="Team Members" />
        <StatCard icon={Flag} tone="blue" value={milestones?.length ?? '—'} label="Milestones" />
        <StatCard
          icon={CalendarClock}
          tone="amber"
          value={daysRemaining !== null ? Math.max(daysRemaining, 0) : '—'}
          label="Days Remaining"
        />
        <Link to={`/projects/${id}/progress`} className="block">
          <Card className="flex h-full items-center justify-center gap-2 text-blue-600 transition-shadow hover:shadow-md">
            <ClipboardList className="size-5" />
            <span className="font-semibold">View Plan</span>
          </Card>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Team</CardTitle>
        </CardHeader>
        <CardContent>
          <TeamMembersSection projectId={id} />
        </CardContent>
      </Card>
    </div>
  )
}

export { ProjectDetailPage }
