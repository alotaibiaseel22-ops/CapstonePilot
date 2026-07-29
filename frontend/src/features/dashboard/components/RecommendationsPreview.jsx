import { Sparkles } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'

const badgeTone = { high: 'destructive', medium: 'warning', low: 'default' }
const severityLabel = { high: 'High', medium: 'Medium', low: 'Low' }

function RecommendationsPreview({ recommendations = [] }) {
  const preview = recommendations.slice(0, 3)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-purple-600" />
          AI Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {preview.length === 0 ? (
          <p className="text-sm text-muted-foreground">No pending recommendations right now.</p>
        ) : (
          preview.map((rec) => (
            <div key={rec.id} className="rounded-lg border border-border p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-gray-900">{rec.title}</p>
                <Badge variant={badgeTone[rec.severity]} className="shrink-0">
                  {severityLabel[rec.severity] ?? rec.severity}
                </Badge>
              </div>
              {rec.description && <p className="mt-1 text-sm text-muted-foreground">{rec.description}</p>}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}

export { RecommendationsPreview }
