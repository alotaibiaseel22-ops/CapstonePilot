import { CheckCircle2, Circle, CircleDot } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { cn } from '@/shared/lib/utils'

const priorityTone = { high: 'destructive', medium: 'warning', low: 'default' }
const priorityLabel = { high: 'High', medium: 'Medium', low: 'Low' }

const statusMeta = {
  pending: { label: 'Pending', tone: 'default', color: 'gray', value: 0, icon: Circle },
  in_progress: { label: 'In Progress', tone: 'info', color: 'blue', value: 50, icon: CircleDot },
  done: { label: 'Done', tone: 'success', color: 'green', value: 100, icon: CheckCircle2 },
}

const NEXT_STATUS = { pending: 'in_progress', in_progress: 'done', done: 'pending' }

function TaskRow({ task, onStatusChange, updating }) {
  const meta = statusMeta[task.status]
  const StatusIcon = meta.icon
  const done = task.status === 'done'

  return (
    <div className="flex items-center gap-3 border-t border-border px-6 py-4">
      <button
        type="button"
        onClick={() => onStatusChange(NEXT_STATUS[task.status])}
        disabled={updating}
        aria-label={`Advance status for ${task.title}`}
        className="shrink-0 disabled:opacity-50"
      >
        <StatusIcon
          className={cn(
            'size-5',
            done ? 'text-green-600' : task.status === 'in_progress' ? 'text-blue-500' : 'text-gray-300',
          )}
        />
      </button>
      <p className={cn('flex-1 text-sm text-gray-800', done && 'text-muted-foreground line-through')}>
        {task.title}
      </p>
      <Badge variant={priorityTone[task.priority]}>{priorityLabel[task.priority]}</Badge>
      <Badge variant={meta.tone}>{meta.label}</Badge>
      <Progress value={meta.value} color={meta.color} className="w-24" />
      <span className="w-10 shrink-0 text-right text-sm text-muted-foreground">{meta.value}%</span>
    </div>
  )
}

export { TaskRow }
