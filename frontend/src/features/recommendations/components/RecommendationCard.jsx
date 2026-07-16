import { useState } from 'react'
import { Bot, ChevronDown, ChevronRight, Check, X } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'

const severityTone = { Critical: 'destructive', High: 'warning' }
const effortTone = { Low: 'text-green-600', Medium: 'text-amber-600', High: 'text-red-600' }
const impactTone = { Low: 'text-green-600', Medium: 'text-amber-600', High: 'text-red-600' }

function RecommendationCard({ title, severity, category, effort, impact, description, rationale, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const [decision, setDecision] = useState(null)

  return (
    <Card>
      <CardContent className="flex gap-4">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-600">
          <Bot className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="font-bold text-gray-900">{title}</p>
            {rationale && (
              <button type="button" onClick={() => setOpen((v) => !v)} aria-label="Toggle details">
                {open ? (
                  <ChevronDown className="size-5 shrink-0 text-gray-400" />
                ) : (
                  <ChevronRight className="size-5 shrink-0 text-gray-400" />
                )}
              </button>
            )}
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <Badge variant={severityTone[severity]}>{severity}</Badge>
            <Badge>{category}</Badge>
            <span className="text-muted-foreground">
              Effort: <span className={effortTone[effort]}>{effort}</span>
            </span>
            <span className="text-muted-foreground">
              Impact: <span className={impactTone[impact]}>{impact}</span>
            </span>
          </div>

          <p className="mt-3 text-sm text-gray-700">{description}</p>

          {open && rationale && (
            <div className="mt-4 rounded-lg bg-gray-50 p-4">
              <p className="text-xs font-semibold tracking-wide text-gray-500">AI RATIONALE</p>
              <p className="mt-1 text-sm text-gray-800">{rationale}</p>
            </div>
          )}

          <div className="mt-4 flex gap-3">
            <Button
              type="button"
              variant="success"
              size="sm"
              onClick={() => setDecision('accepted')}
              disabled={decision !== null}
            >
              <Check className="size-4" />
              {decision === 'accepted' ? 'Accepted' : 'Accept'}
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={() => setDecision('dismissed')}
              disabled={decision !== null}
            >
              <X className="size-4" />
              {decision === 'dismissed' ? 'Dismissed' : 'Dismiss'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export { RecommendationCard }
