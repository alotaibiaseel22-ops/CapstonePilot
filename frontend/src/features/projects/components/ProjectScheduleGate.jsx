import { Outlet, useParams } from 'react-router-dom'
import { CalendarClock } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProject } from '../hooks/useProjects'
import { ProjectScheduleDialog } from './ProjectScheduleDialog'

// Wraps the AI monitoring routes - Risk Analysis and Recommendations only
// (see router.jsx) - with a single "does this project have a deadline yet"
// check. Schedule-based analysis is meaningless without one - the scheduler
// itself refuses to run it for a project with no due_date (see
// scheduler.py::_check_project) - so this blocks access to those two pages
// until the owner sets one, rather than letting the user reach a page full
// of misleading empty states. Everything else about using a project (Share,
// Settings, Plan approval) is unaffected - only the two AI monitoring
// surfaces are gated.
function ProjectScheduleGate() {
  const { id } = useParams()
  const { user } = useAuth()
  const { data: project, isLoading, isError } = useProject(id)

  if (isLoading) return <LoadingState label="Loading project..." />
  if (isError || !project) {
    return <ErrorState message="Couldn't load this project. Please try again." />
  }

  if (project.due_date) {
    return <Outlet />
  }

  const isOwner = user?.id === project.owner_id
  if (isOwner) {
    return <ProjectScheduleDialog projectId={project.id} />
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <CalendarClock className="size-8 text-muted-foreground" />
      <div>
        <p className="font-semibold text-gray-900">Project schedule not set yet</p>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Waiting for the project owner to set a start date and submission deadline before AI
          monitoring becomes available.
        </p>
      </div>
    </div>
  )
}

export { ProjectScheduleGate }
