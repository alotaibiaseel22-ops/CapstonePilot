import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/card'
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
      <CardContent>
        <ProgressOverviewChart />
      </CardContent>
    </Card>
  )
}

export { ProgressOverviewCard }
