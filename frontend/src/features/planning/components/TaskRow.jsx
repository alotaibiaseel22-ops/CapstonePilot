import { CheckCircle2, Circle } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { cn } from '@/shared/lib/utils'

const priorityTone = { High: 'destructive', Medium: 'warning' }
const statusTone = { Done: 'success', 'In Progress': 'info', Pending: 'default' }
const statusColor = { Done: 'green', 'In Progress': 'blue', Pending: 'gray' }

function TaskRow({ title, priority, status, value }) {
  const done = status === 'Done'

  return (
    <div className="flex items-center gap-3 border-t border-border px-6 py-4">
      {done ? (
        <CheckCircle2 className="size-5 shrink-0 text-green-600" />
      ) : (
        <Circle className="size-5 shrink-0 text-gray-300" />
      )}
      <p className={cn('flex-1 text-sm text-gray-800', done && 'text-muted-foreground line-through')}>{title}</p>
      <Badge variant={priorityTone[priority]}>{priority}</Badge>
      <Badge variant={statusTone[status]}>{status}</Badge>
      <Progress value={value} color={statusColor[status]} className="w-24" />
      <span className="w-10 shrink-0 text-right text-sm text-muted-foreground">{value}%</span>
    </div>
  )
}

export { TaskRow }
