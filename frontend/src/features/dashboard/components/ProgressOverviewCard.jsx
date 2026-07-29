import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/card'
import { PreviewDataBanner } from '@/shared/components/common/PreviewDataBanner'
import { ProgressOverviewChart } from './ProgressOverviewChart'

function ProgressOverviewCard() {
  return (
    <Card>
      <CardHeader className="items-start">
        <div>
          <CardTitle>Progress Overview</CardTitle>
          <CardDescription>Task completion over 8 weeks</CardDescription>
        </div>
        <span className="flex items-center gap-2 text-sm text-gray-600">
          <span className="size-2 rounded-full bg-blue-600" />
          Completion %
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        <PreviewDataBanner>
          Preview data — there's no historical progress tracking yet, only the current snapshot
          shown elsewhere on this Dashboard.
        </PreviewDataBanner>
        <ProgressOverviewChart />
      </CardContent>
    </Card>
  )
}

export { ProgressOverviewCard }
