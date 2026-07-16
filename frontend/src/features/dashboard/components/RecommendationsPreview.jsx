import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'

const badgeTone = { High: 'destructive', Medium: 'warning' }

const recommendations = [
  {
    title: 'Start testing earlier',
    severity: 'High',
    description: 'Testing phase is currently planned for week 10. AI models predict 34% risk of la...',
  },
  {
    title: 'Implementation phase behind schedule',
    severity: 'Medium',
    description: '3 backend tasks are overdue by an average of 4 days. Recommend escalating to sup...',
  },
  {
    title: 'Redistribute tasks between team members',
    severity: 'Medium',
    description: 'Omar has 7 open tasks while Priya has 2. Rebalancing workload could accelerate d...',
  },
]

function RecommendationsPreview() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-purple-600" />
          AI Recommendations
        </CardTitle>
        <Link to="/recommendations" className="flex items-center gap-1 text-sm font-medium text-blue-600 hover:underline">
          View all
          <ArrowRight className="size-4" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {recommendations.map((rec) => (
          <div key={rec.title} className="rounded-lg border border-border p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-semibold text-gray-900">{rec.title}</p>
              <Badge variant={badgeTone[rec.severity]} className="shrink-0">
                {rec.severity}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{rec.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export { RecommendationsPreview }
