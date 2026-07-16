import { CheckCircle2, Clock, ChevronRight } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Progress } from '@/shared/components/ui/progress'
import { cn } from '@/shared/lib/utils'

const milestones = [
  { title: 'Requirements Finalization', value: 100, date: 'Jul 12, 2026', done: true },
  { title: 'System Architecture Design', value: 85, date: 'Jul 19, 2026', done: false },
  { title: 'Backend API Development', value: 48, date: 'Aug 2, 2026', done: false },
  { title: 'Frontend Integration', value: 10, date: 'Aug 16, 2026', done: false },
  { title: 'Testing & QA', value: 0, date: 'Sep 1, 2026', done: false },
]

function progressColor(value) {
  if (value >= 80) return 'green'
  if (value > 0) return 'amber'
  return 'gray'
}

function MilestonesPreview() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Milestones</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {milestones.map((m) => (
          <div key={m.title}>
            <div className="flex items-center gap-2">
              {m.done ? (
                <CheckCircle2 className="size-4 shrink-0 text-green-600" />
              ) : (
                <Clock className="size-4 shrink-0 text-gray-400" />
              )}
              <p className={cn('flex-1 truncate text-sm text-gray-800', m.done && 'text-muted-foreground line-through')}>
                {m.title}
              </p>
              <span className="text-sm text-muted-foreground">{m.value}%</span>
            </div>
            <div className="mt-1.5 flex items-center gap-2 pl-6">
              <Progress value={m.value} color={progressColor(m.value)} className="flex-1" />
              <span className="flex shrink-0 items-center gap-0.5 text-xs text-muted-foreground">
                <ChevronRight className="size-3" />
                {m.date}
              </span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export { MilestonesPreview }
