import { ShieldAlert, ChevronDown } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'

const severityTone = {
  High: { badge: 'destructive', icon: 'bg-red-100 text-red-600' },
  Medium: { badge: 'warning', icon: 'bg-amber-100 text-amber-600' },
  Low: { badge: 'success', icon: 'bg-green-100 text-green-600' },
}

function RiskCard({ title, severity, category, date, description }) {
  const tone = severityTone[severity]

  return (
    <Card>
      <CardContent className="flex gap-4">
        <span className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${tone.icon}`}>
          <ShieldAlert className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="font-bold text-gray-900">{title}</p>
            <ChevronDown className="size-5 shrink-0 text-gray-400" />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge variant={tone.badge}>{severity} Risk</Badge>
            <Badge>{category}</Badge>
            <span className="text-sm text-muted-foreground">&middot; {date}</span>
          </div>
          <p className="mt-3 text-sm text-gray-700">{description}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export { RiskCard }
