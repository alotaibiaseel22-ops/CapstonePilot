import { useState } from 'react'
import { Flag, ChevronDown, ChevronRight } from 'lucide-react'
import { Card } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { useTasks, useUpdateTaskStatus, useAssignTask } from '../hooks/useTasks'
import { TaskRow } from './TaskRow'

function progressTone(value) {
  if (value === 100) return { bar: 'green', badge: 'bg-green-100 text-green-600' }
  if (value === 0) return { bar: 'gray', badge: 'bg-gray-100 text-gray-400' }
  if (value >= 50) return { bar: 'blue', badge: 'bg-blue-100 text-blue-600' }
  return { bar: 'amber', badge: 'bg-blue-100 text-blue-600' }
}

function formatDate(value) {
  if (!value) return null
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function MilestoneAccordion({ milestone, defaultOpen = false, members = [], guests = [] }) {
  const [open, setOpen] = useState(defaultOpen)
  // Always fetched (not gated on `open`) so the collapsed header's progress
  // summary is accurate immediately, not just after the user expands it.
  const { data: tasks, isLoading } = useTasks(milestone.id)
  const updateStatus = useUpdateTaskStatus(milestone.id)
  const assignTask = useAssignTask(milestone.id)

  const done = tasks?.filter((t) => t.status === 'done').length ?? 0
  const total = tasks?.length ?? 0
  const value = total > 0 ? Math.round((done / total) * 100) : 0
  const tone = progressTone(value)
  const complete = total > 0 && done === total

  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        data-testid="milestone-accordion-toggle"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-4 p-6 text-left"
      >
        <span className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${tone.badge}`}>
          <Flag className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="font-bold text-gray-900">{milestone.title}</p>
            {complete && <Badge variant="success">Complete</Badge>}
          </div>
          <div className="mt-2 flex items-center gap-3">
            <Progress value={value} color={tone.bar} className="max-w-xs" />
            <span className="shrink-0 text-sm font-medium text-gray-700">{value}%</span>
            {milestone.due_date && (
              <span className="shrink-0 text-sm text-muted-foreground">Due {formatDate(milestone.due_date)}</span>
            )}
          </div>
        </div>
        {open ? (
          <ChevronDown className="size-5 shrink-0 text-gray-400" />
        ) : (
          <ChevronRight className="size-5 shrink-0 text-gray-400" />
        )}
      </button>

      {open && (
        <div>
          {isLoading && <LoadingState label="Loading tasks..." />}
          {!isLoading && total === 0 && (
            <p className="border-t border-border px-6 py-4 text-sm text-muted-foreground">
              No tasks yet for this milestone.
            </p>
          )}
          {!isLoading &&
            tasks?.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                updating={updateStatus.isPending}
                onStatusChange={(status) => updateStatus.mutate({ taskId: task.id, status })}
                members={members}
                guests={guests}
                onAssign={(assignee) => assignTask.mutate({ taskId: task.id, ...assignee })}
              />
            ))}
        </div>
      )}
    </Card>
  )
}

export { MilestoneAccordion }
