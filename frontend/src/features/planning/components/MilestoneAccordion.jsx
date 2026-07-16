import { useState } from 'react'
import { Flag, ChevronDown, ChevronRight } from 'lucide-react'
import { Card } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { TaskRow } from './TaskRow'

function progressTone(value) {
  if (value === 100) return { bar: 'green', badge: 'bg-green-100 text-green-600' }
  if (value === 0) return { bar: 'gray', badge: 'bg-gray-100 text-gray-400' }
  if (value >= 50) return { bar: 'blue', badge: 'bg-blue-100 text-blue-600' }
  return { bar: 'amber', badge: 'bg-blue-100 text-blue-600' }
}

function MilestoneAccordion({ title, status, value, dueDate, tasks, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const tone = progressTone(value)
  const hasTasks = tasks.length > 0

  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        onClick={() => hasTasks && setOpen((v) => !v)}
        className="flex w-full items-center gap-4 p-6 text-left"
      >
        <span className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${tone.badge}`}>
          <Flag className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="font-bold text-gray-900">{title}</p>
            {status && <Badge variant="success">{status}</Badge>}
          </div>
          <div className="mt-2 flex items-center gap-3">
            <Progress value={value} color={tone.bar} className="max-w-xs" />
            <span className="shrink-0 text-sm font-medium text-gray-700">{value}%</span>
            <span className="shrink-0 text-sm text-muted-foreground">Due {dueDate}</span>
          </div>
        </div>
        {hasTasks &&
          (open ? (
            <ChevronDown className="size-5 shrink-0 text-gray-400" />
          ) : (
            <ChevronRight className="size-5 shrink-0 text-gray-400" />
          ))}
      </button>

      {open && hasTasks && (
        <div>
          {tasks.map((task) => (
            <TaskRow key={task.title} {...task} />
          ))}
        </div>
      )}
    </Card>
  )
}

export { MilestoneAccordion }
