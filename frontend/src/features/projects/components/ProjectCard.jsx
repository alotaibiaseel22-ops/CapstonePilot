import { Link } from 'react-router-dom'
import { Calendar } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { Avatar } from '@/shared/components/ui/avatar'

const healthTone = { Good: 'success', 'At Risk': 'warning', Critical: 'destructive' }
const progressColor = { Good: 'green', 'At Risk': 'amber', Critical: 'red' }

function initialsOf(name) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function ProjectCard({ project }) {
  return (
    <Link to={`/projects/${project.id}`} className="block">
      <Card className="h-full transition-shadow hover:shadow-md">
        <CardContent>
          <div className="flex items-start justify-between gap-2">
            <p className="font-bold text-gray-900">{project.name}</p>
            <Badge variant={healthTone[project.health]} className="shrink-0">
              {project.health}
            </Badge>
          </div>

          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{project.description}</p>

          <div className="mt-4">
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className="text-gray-700">Progress</span>
              <span className="font-semibold text-gray-900">{project.progress}%</span>
            </div>
            <Progress value={project.progress} color={progressColor[project.health]} />
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="flex -space-x-2">
              {project.team.map((member) => (
                <Avatar
                  key={member.name}
                  initials={initialsOf(member.name)}
                  color={member.color}
                  className="ring-2 ring-white"
                />
              ))}
            </div>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar className="size-3.5" />
              {new Date(project.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}

export { ProjectCard }
