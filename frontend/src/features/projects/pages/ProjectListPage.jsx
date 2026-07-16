import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { Button } from '@/shared/components/ui/button'
import { getProjects } from '../api/projects'
import { ProjectCard } from '../components/ProjectCard'

function ProjectListPage() {
  const projects = getProjects()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-muted-foreground">CapstonePilot is monitoring {projects.length} projects</p>
        </div>
        <Link to="/projects/new">
          <Button type="button">
            <Plus className="size-5" />
            New Project
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  )
}

export { ProjectListPage }
