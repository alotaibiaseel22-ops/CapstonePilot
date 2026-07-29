import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Archive,
  ArrowLeft,
  CalendarClock,
  ClipboardList,
  Flag,
  Lightbulb,
  MoreVertical,
  Pencil,
  Share2,
  ShieldAlert,
  Trash2,
  Users,
} from 'lucide-react'
import { StatCard } from '@/shared/components/common/StatCard'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Card } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'
import { ConfirmDialog } from '@/shared/components/ui/confirm-dialog'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProject, useDeleteProject, useUpdateProject } from '../hooks/useProjects'
import { useProjectMembers } from '../hooks/useProjectMembers'
import { useMilestones } from '@/features/planning/hooks/useMilestones'
import { ShareModal } from '../components/ShareModal'

const statusTone = { planning: 'default', active: 'info', completed: 'success', archived: 'default' }
const statusLabel = { planning: 'Planning', active: 'Active', completed: 'Completed', archived: 'Archived' }

function ProjectDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data: project, isLoading, isError } = useProject(id)
  const { data: members } = useProjectMembers(id)
  const { data: milestones } = useMilestones(id)
  const deleteProject = useDeleteProject()
  const updateProject = useUpdateProject(id)

  const [shareOpen, setShareOpen] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

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
  const isOwner = user?.id === project.owner_id

  const isArchived = project.status === 'archived'

  async function handleDelete() {
    await deleteProject.mutateAsync(id)
    navigate('/projects', { replace: true })
  }

  function handleToggleArchive() {
    updateProject.mutate({ status: isArchived ? 'active' : 'archived' })
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Link
          to="/projects"
          className="flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-gray-700"
        >
          <ArrowLeft className="size-4" />
          Back to Projects
        </Link>

        <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Link to="/projects" className="hover:text-gray-700">
            Projects
          </Link>
          <span>/</span>
          <span className="font-medium text-gray-700">{project.name}</span>
        </nav>
      </div>

      {isArchived && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          This project is archived. CapstonePilot has paused automatic risk monitoring for it -
          unarchive it to resume.
        </div>
      )}

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
            <Badge variant={statusTone[project.status]}>{statusLabel[project.status] ?? project.status}</Badge>
          </div>
          <p className="mt-2 max-w-3xl text-muted-foreground">
            {project.description || 'No description provided.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" onClick={() => setShareOpen(true)}>
            <Share2 className="size-4" />
            Share
          </Button>

          {isOwner && (
            <DropdownMenu
              trigger={(triggerProps) => (
                <button
                  type="button"
                  aria-label="Project actions"
                  className="flex size-10 items-center justify-center rounded-lg border border-border text-gray-500 hover:bg-muted hover:text-gray-700"
                  {...triggerProps}
                >
                  <MoreVertical className="size-4" />
                </button>
              )}
            >
              <DropdownMenuItem icon={Pencil} onClick={() => navigate(`/projects/${id}/settings`)}>
                Edit Project
              </DropdownMenuItem>
              <DropdownMenuItem icon={Archive} onClick={handleToggleArchive}>
                {isArchived ? 'Unarchive Project' : 'Archive Project'}
              </DropdownMenuItem>
              <DropdownMenuItem icon={Trash2} destructive onClick={() => setConfirmingDelete(true)}>
                Delete Project
              </DropdownMenuItem>
            </DropdownMenu>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} tone="purple" value={members?.length ?? '—'} label="Collaborators" />
        <StatCard icon={Flag} tone="blue" value={milestones?.length ?? '—'} label="Milestones" />
        <StatCard
          icon={CalendarClock}
          tone="amber"
          value={daysRemaining !== null ? Math.max(daysRemaining, 0) : 'Deadline not set'}
          label="Days Remaining"
        />
        <Link to={`/projects/${id}/progress`} className="block">
          <Card className="flex h-full items-center justify-center gap-2 text-blue-600 transition-shadow hover:shadow-md">
            <ClipboardList className="size-5" />
            <span className="font-semibold">View Plan</span>
          </Card>
        </Link>
        <Link to={`/projects/${id}/risks`} className="block">
          <Card className="flex h-full items-center justify-center gap-2 text-blue-600 transition-shadow hover:shadow-md">
            <ShieldAlert className="size-5" />
            <span className="font-semibold">View Risks</span>
          </Card>
        </Link>
        <Link to={`/projects/${id}/recommendations`} className="block">
          <Card className="flex h-full items-center justify-center gap-2 text-blue-600 transition-shadow hover:shadow-md">
            <Lightbulb className="size-5" />
            <span className="font-semibold">View Recommendations</span>
          </Card>
        </Link>
      </div>

      <ShareModal open={shareOpen} onClose={() => setShareOpen(false)} project={project} />

      <ConfirmDialog
        open={confirmingDelete}
        onClose={() => setConfirmingDelete(false)}
        onConfirm={handleDelete}
        title="Delete project"
        description={`This will permanently delete "${project.name}" and everything in it. This can't be undone.`}
        confirmLabel="Delete project"
        destructive
        isConfirming={deleteProject.isPending}
      />
    </div>
  )
}

export { ProjectDetailPage }
