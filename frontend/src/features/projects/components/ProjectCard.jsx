import { Link } from 'react-router-dom'
import { Calendar } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'

const statusTone = { planning: 'default', active: 'info', completed: 'success' }
const statusLabel = { planning: 'Planning', active: 'Active', completed: 'Completed' }

function formatDate(value) {
  if (!value) return null
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function ProjectCard({ project }) {
  return (
    <Link to={`/projects/${project.id}`} className="block">
      <Card className="h-full transition-shadow hover:shadow-md">
        <CardContent>
          <div className="flex items-start justify-between gap-2">
            <p className="font-bold text-gray-900">{project.name}</p>
            <Badge variant={statusTone[project.status]} className="shrink-0">
              {statusLabel[project.status] ?? project.status}
            </Badge>
          </div>

          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {project.description || 'No description provided.'}
          </p>

          {project.due_date && (
            <div className="mt-4 flex items-center justify-end">
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Calendar className="size-3.5" />
                Due {formatDate(project.due_date)}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}

export { ProjectCard }
