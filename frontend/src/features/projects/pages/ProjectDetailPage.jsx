import { useParams, Link } from 'react-router-dom'
import { TrendingUp, Users, FileText, CalendarClock } from 'lucide-react'
import { StatCard } from '@/shared/components/common/StatCard'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Avatar } from '@/shared/components/ui/avatar'
import { Button } from '@/shared/components/ui/button'
import { getProjectById } from '../api/projects'
import { DocumentsCard } from '../components/DocumentsCard'

const healthTone = { Good: 'success', 'At Risk': 'warning', Critical: 'destructive' }
const TODAY = new Date('2026-07-09')

function initialsOf(name) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function ProjectDetailPage() {
  const { id } = useParams()
  const project = getProjectById(id)

  if (!project) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Project not found</h1>
        <p className="text-muted-foreground">This project doesn't exist or may have been removed.</p>
        <Link to="/projects">
          <Button type="button" variant="outline">
            Back to Projects
          </Button>
        </Link>
      </div>
    )
  }

  const daysRemaining = Math.ceil((new Date(project.dueDate) - TODAY) / (1000 * 60 * 60 * 24))

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <Badge variant={healthTone[project.health]}>{project.health}</Badge>
          <Badge>{project.status}</Badge>
        </div>
        <p className="mt-2 max-w-3xl text-muted-foreground">{project.description}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={TrendingUp} tone="blue" value={`${project.progress}%`} label="Progress" />
        <StatCard icon={Users} tone="purple" value={project.team.length} label="Team Members" />
        <StatCard icon={FileText} tone="green" value={project.documents.length} label="Documents" />
        <StatCard
          icon={CalendarClock}
          tone="amber"
          value={daysRemaining > 0 ? daysRemaining : 0}
          label="Days Remaining"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Team</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {project.team.map((member) => (
              <div key={member.name} className="flex items-center gap-3">
                <Avatar initials={initialsOf(member.name)} color={member.color} />
                <span className="text-sm font-medium text-gray-800">{member.name}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="xl:col-span-2">
          <DocumentsCard initialDocuments={project.documents} />
        </div>
      </div>
    </div>
  )
}

export { ProjectDetailPage }
