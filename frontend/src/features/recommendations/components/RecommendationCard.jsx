import { useState } from 'react'
import { Bot, ChevronDown, ChevronRight, Check, X } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { useApproveRecommendation, useRejectRecommendation } from '../hooks/useRecommendations'

const severityTone = { high: 'destructive', medium: 'warning', low: 'default' }
const severityLabel = { high: 'High', medium: 'Medium', low: 'Low' }
const tierTone = { low: 'text-green-600', medium: 'text-amber-600', high: 'text-red-600' }
const tierLabel = { low: 'Low', medium: 'Medium', high: 'High' }

function RecommendationCard({
  id,
  projectId,
  title,
  category,
  severity,
  effort,
  impact,
  description,
  rationale,
  status,
}) {
  const [open, setOpen] = useState(false)
  const approve = useApproveRecommendation(projectId)
  const reject = useRejectRecommendation(projectId)
  const isPending = status === 'pending'
  const isMutating = approve.isPending || reject.isPending

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
            <Badge variant={severityTone[severity]}>{severityLabel[severity] ?? severity}</Badge>
            <Badge>{category}</Badge>
            <span className="text-muted-foreground">
              Effort: <span className={tierTone[effort]}>{tierLabel[effort] ?? effort}</span>
            </span>
            <span className="text-muted-foreground">
              Impact: <span className={tierTone[impact]}>{tierLabel[impact] ?? impact}</span>
            </span>
          </div>

          {description && <p className="mt-3 text-sm text-gray-700">{description}</p>}

          {open && rationale && (
            <div className="mt-4 rounded-lg bg-gray-50 p-4">
              <p className="text-xs font-semibold tracking-wide text-gray-500">AI RATIONALE</p>
              <p className="mt-1 text-sm text-gray-800">{rationale}</p>
            </div>
          )}

          <div className="mt-4 flex gap-3">
            {isPending ? (
              <>
                <Button
                  type="button"
                  variant="success"
                  size="sm"
                  onClick={() => approve.mutate(id)}
                  disabled={isMutating}
                >
                  <Check className="size-4" />
                  Accept
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={() => reject.mutate(id)}
                  disabled={isMutating}
                >
                  <X className="size-4" />
                  Dismiss
                </Button>
              </>
            ) : (
              <Badge variant={status === 'approved' ? 'success' : 'default'}>
                {status === 'approved' ? 'Accepted' : 'Dismissed'}
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export { RecommendationCard }
