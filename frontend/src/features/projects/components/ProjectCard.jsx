import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Calendar, FolderOpen, MoreVertical, Pencil, Trash2 } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'
import { ConfirmDialog } from '@/shared/components/ui/confirm-dialog'
import { useAuth } from '@/app/providers/AuthProvider'
import { useDeleteProject } from '../hooks/useProjects'

const statusTone = { planning: 'default', active: 'info', completed: 'success', archived: 'default' }
const statusLabel = { planning: 'Planning', active: 'Active', completed: 'Completed', archived: 'Archived' }

function formatDate(value) {
  if (!value) return null
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function ProjectCard({ project }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const deleteProject = useDeleteProject()
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const isOwner = user?.id === project.owner_id

  async function handleDelete() {
    await deleteProject.mutateAsync(project.id)
    setConfirmingDelete(false)
  }

  return (
    <Card className="relative h-full transition-shadow hover:shadow-md" data-testid="project-card">
      {isOwner && (
        <div className="absolute right-3 top-3 z-10">
          <DropdownMenu
            trigger={(triggerProps) => (
              <button
                type="button"
                aria-label="Project actions"
                className="rounded-md p-1 text-gray-400 hover:bg-muted hover:text-gray-700"
                {...triggerProps}
              >
                <MoreVertical className="size-4" />
              </button>
            )}
          >
            <DropdownMenuItem icon={FolderOpen} onClick={() => navigate(`/projects/${project.id}`)}>
              Open
            </DropdownMenuItem>
            <DropdownMenuItem
              icon={Pencil}
              onClick={() => navigate(`/projects/${project.id}/settings`)}
            >
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem icon={Trash2} destructive onClick={() => setConfirmingDelete(true)}>
              Delete
            </DropdownMenuItem>
          </DropdownMenu>
        </div>
      )}

      <Link to={`/projects/${project.id}`} className="block">
        <CardContent>
          <div className="flex items-start justify-between gap-2 pr-6">
            <p className="font-bold text-gray-900">{project.name}</p>
            <Badge variant={statusTone[project.status]} className="shrink-0">
              {statusLabel[project.status] ?? project.status}
            </Badge>
          </div>

          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {project.description || 'No description provided.'}
          </p>

          <div className="mt-4 flex items-center justify-end">
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar className="size-3.5" />
              {project.due_date ? `Due ${formatDate(project.due_date)}` : 'Deadline not set'}
            </span>
          </div>
        </CardContent>
      </Link>

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
    </Card>
  )
}

export { ProjectCard }
