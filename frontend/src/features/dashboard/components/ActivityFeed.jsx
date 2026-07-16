import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { cn } from '@/shared/lib/utils'

const ringColors = {
  red: 'border-red-500',
  green: 'border-green-500',
  purple: 'border-purple-500',
  gray: 'border-gray-300',
}

const activity = [
  {
    ring: 'red',
    text: 'AI agent flagged implementation delay in ML Classifier',
    meta: '09:24 AM · AI Agent',
  },
  {
    ring: 'green',
    text: 'Omar Al-Rashidi completed "Database Schema Design" task',
    meta: '08:50 AM · Omar A.',
  },
  {
    ring: 'purple',
    text: 'New recommendation: Redistribute backend tasks to reduce bottleneck',
    meta: 'Yesterday · AI Agent',
  },
  {
    ring: 'gray',
    text: 'Milestone "API Integration" marked as in-progress',
    meta: 'Yesterday · Lena Fischer',
  },
  {
    ring: 'gray',
    text: 'Sprint 3 retrospective notes uploaded',
    meta: 'Mon, Jul 7 · Priya Nair',
  },
]

function ActivityFeed() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {activity.map((item, i) => (
          <div key={i} className="flex gap-3">
            <span className={cn('mt-1 size-2.5 shrink-0 rounded-full border-2', ringColors[item.ring])} />
            <div>
              <p className="text-sm text-gray-800">{item.text}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{item.meta}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export { ActivityFeed }
