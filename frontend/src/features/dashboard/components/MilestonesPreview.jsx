import { CheckCircle2, Clock, ChevronRight } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Progress } from '@/shared/components/ui/progress'
import { cn } from '@/shared/lib/utils'

function progressColor(value) {
  if (value >= 80) return 'green'
  if (value > 0) return 'amber'
  return 'gray'
}

function formatDate(value) {
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function MilestonesPreview({ milestones = [] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Milestones</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {milestones.length === 0 ? (
          <p className="text-sm text-muted-foreground">No upcoming milestones.</p>
        ) : (
          milestones.map((m) => (
            <div key={m.id}>
              <div className="flex items-center gap-2">
                {m.done ? (
                  <CheckCircle2 className="size-4 shrink-0 text-green-600" />
                ) : (
                  <Clock className="size-4 shrink-0 text-gray-400" />
                )}
                <p
                  className={cn(
                    'flex-1 truncate text-sm text-gray-800',
                    m.done && 'text-muted-foreground line-through',
                  )}
                >
                  {m.title}
                </p>
                <span className="text-sm text-muted-foreground">{m.value}%</span>
              </div>
              <div className="mt-1.5 flex items-center gap-2 pl-6">
                <Progress value={m.value} color={progressColor(m.value)} className="flex-1" />
                <span className="flex shrink-0 items-center gap-0.5 text-xs text-muted-foreground">
                  <ChevronRight className="size-3" />
                  {formatDate(m.due_date)}
                </span>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}

export { MilestonesPreview }
