import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { useActivity } from '@/features/activity/hooks/useActivity'
import { cn } from '@/shared/lib/utils'

const ringColors = {
  project_created: 'gray',
  plan_generated: 'purple',
  plan_approved: 'green',
  plan_rejected: 'red',
  task_completed: 'green',
  risk_detected: 'red',
  recommendation_approved: 'green',
  recommendation_rejected: 'gray',
  member_joined: 'gray',
}

const ringBorderClasses = {
  red: 'border-red-500',
  green: 'border-green-500',
  purple: 'border-purple-500',
  gray: 'border-gray-300',
}

function formatMeta(createdAt) {
  return new Date(createdAt).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function ActivityFeed() {
  const { data: events, isLoading } = useActivity(8)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading activity...</p>
        ) : events.length === 0 ? (
          <p className="text-sm text-muted-foreground">No activity yet.</p>
        ) : (
          events.map((event) => (
            <div key={event.id} className="flex gap-3">
              <span
                className={cn(
                  'mt-1 size-2.5 shrink-0 rounded-full border-2',
                  ringBorderClasses[ringColors[event.event_type] ?? 'gray'],
                )}
              />
              <div>
                <p className="text-sm text-gray-800">{event.message}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{formatMeta(event.created_at)}</p>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}

export { ActivityFeed }
