import { ShieldAlert } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'

const severityTone = {
  high: { badge: 'destructive', icon: 'bg-red-100 text-red-600' },
  medium: { badge: 'warning', icon: 'bg-amber-100 text-amber-600' },
  low: { badge: 'success', icon: 'bg-green-100 text-green-600' },
}

const severityLabel = { high: 'High', medium: 'Medium', low: 'Low' }

function formatDate(value) {
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function RiskCard({ severity, category, title, description, created_at }) {
  const tone = severityTone[severity] ?? severityTone.medium

  return (
    <Card>
      <CardContent className="flex gap-4">
        <span
          className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${tone.icon}`}
        >
          <ShieldAlert className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-bold text-gray-900">{title}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge variant={tone.badge}>{severityLabel[severity] ?? severity} Risk</Badge>
            <Badge>{category}</Badge>
            <span className="text-sm text-muted-foreground">&middot; {formatDate(created_at)}</span>
          </div>
          {description && <p className="mt-3 text-sm text-gray-700">{description}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

export { RiskCard }
