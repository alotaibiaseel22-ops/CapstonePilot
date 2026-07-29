import { useState } from 'react'
import { CalendarClock } from 'lucide-react'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { useUpdateProject } from '../hooks/useProjects'

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10)
}

// Deliberately not built on the shared Modal - this dialog has no close
// button and doesn't dismiss on backdrop click or Escape. While a project
// has no deadline, AI monitoring (Dashboard metrics, Risk Analysis,
// Recommendations) is blocked until the owner sets one - see
// ProjectScheduleGate, which is this dialog's only caller.
function ProjectScheduleDialog({ projectId, onSaved }) {
  const updateProject = useUpdateProject(projectId)
  const [startDate, setStartDate] = useState(todayIsoDate())
  const [dueDate, setDueDate] = useState('')
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!dueDate || updateProject.isPending) return
    setError(null)
    try {
      await updateProject.mutateAsync({ start_date: startDate, due_date: dueDate })
      onSaved?.()
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Could not save the project schedule.')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-white p-6 shadow-xl">
        <div className="mb-1 flex items-center gap-2">
          <CalendarClock className="size-5 text-blue-600" />
          <h2 className="text-lg font-bold text-gray-900">Set the Project Schedule</h2>
        </div>
        <p className="mb-6 text-sm text-muted-foreground">
          This project needs a start date and submission deadline before AI monitoring can
          begin - it's what powers Days Remaining, progress tracking, risk prediction, and
          recommendations.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
              START DATE
            </label>
            <Input
              type="date"
              required
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
              SUBMISSION DEADLINE
            </label>
            <Input
              type="date"
              required
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button
            type="submit"
            size="lg"
            className="w-full"
            disabled={!dueDate || updateProject.isPending}
          >
            {updateProject.isPending ? 'Saving...' : 'Save Schedule'}
          </Button>
        </form>
      </div>
    </div>
  )
}

export { ProjectScheduleDialog }
