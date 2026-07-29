import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { ConfirmDialog } from '@/shared/components/ui/confirm-dialog'
import { usePlan, useApprovePlan, useRejectPlan } from '../hooks/usePlan'

function PlanApprovalBanner({ projectId, isOwner }) {
  const { data: plan } = usePlan(projectId)
  const approvePlan = useApprovePlan(projectId)
  const rejectPlan = useRejectPlan(projectId)
  const [confirmingReject, setConfirmingReject] = useState(false)

  if (!plan || plan.status !== 'proposed') return null

  async function handleConfirmReject() {
    await rejectPlan.mutateAsync()
    setConfirmingReject(false)
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
        <div className="flex items-start gap-3">
          <Sparkles className="mt-0.5 size-5 shrink-0 text-amber-600" />
          <div>
            <p className="font-semibold text-gray-900">AI-generated plan awaiting your review</p>
            {plan.rationale?.summary && (
              <p className="mt-0.5 text-sm text-muted-foreground">{plan.rationale.summary}</p>
            )}
          </div>
        </div>

        {isOwner ? (
          <div className="flex shrink-0 items-center gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmingReject(true)}
              disabled={rejectPlan.isPending}
            >
              Reject
            </Button>
            <Button
              type="button"
              onClick={() => approvePlan.mutate()}
              disabled={approvePlan.isPending}
            >
              {approvePlan.isPending ? 'Approving...' : 'Approve'}
            </Button>
          </div>
        ) : (
          <Badge variant="warning">Awaiting owner approval</Badge>
        )}
      </div>

      <ConfirmDialog
        open={confirmingReject}
        onClose={() => setConfirmingReject(false)}
        onConfirm={handleConfirmReject}
        title="Reject this plan"
        description="This deletes the AI-generated milestones and tasks and resets the plan to a blank draft. This can't be undone."
        confirmLabel="Reject plan"
        destructive
        isConfirming={rejectPlan.isPending}
      />
    </>
  )
}

export { PlanApprovalBanner }
