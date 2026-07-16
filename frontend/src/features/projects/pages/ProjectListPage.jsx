import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { Button } from '@/shared/components/ui/button'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { useProjects } from '../hooks/useProjects'
import { ProjectCard } from '../components/ProjectCard'

function ProjectListPage() {
  const { data: projects, isLoading, isError } = useProjects()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-muted-foreground">
            {isLoading
              ? 'Loading your projects...'
              : `CapstonePilot is monitoring ${projects?.length ?? 0} project${projects?.length === 1 ? '' : 's'}`}
          </p>
        </div>
        <Link to="/projects/new">
          <Button type="button">
            <Plus className="size-5" />
            New Project
          </Button>
        </Link>
      </div>

      {isLoading && <LoadingState label="Loading projects..." />}
      {isError && <ErrorState message="Couldn't load projects. Please try again." />}

      {!isLoading && !isError && projects?.length === 0 && (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border py-16 text-center text-muted-foreground">
          <p>No projects yet. Create your first one to get started.</p>
          <Link to="/projects/new">
            <Button type="button">
              <Plus className="size-5" />
              Create Project
            </Button>
          </Link>
        </div>
      )}

      {!isLoading && !isError && projects?.length > 0 && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  )
}

export { ProjectListPage }
