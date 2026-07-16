import { TrendingUp, CircleCheck, TriangleAlert, Lightbulb } from 'lucide-react'
import { StatCard } from '@/shared/components/common/StatCard'
import { ProjectHealthCard } from '../components/ProjectHealthCard'
import { ProgressOverviewCard } from '../components/ProgressOverviewCard'
import { ActivityFeed } from '../components/ActivityFeed'
import { RecommendationsPreview } from '../components/RecommendationsPreview'
import { MilestonesPreview } from '../components/MilestonesPreview'

function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          CapstonePilot is actively monitoring your projects &middot; Wednesday, July 9, 2026
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={TrendingUp} tone="blue" value="72%" label="Project Progress" delta="+8% this week" />
        <StatCard icon={CircleCheck} tone="green" value="35" label="Completed Tasks" delta="4 completed today" />
        <StatCard icon={TriangleAlert} tone="amber" value="6" label="Detected Risks" delta="2 new this week" deltaTone="amber" />
        <StatCard icon={Lightbulb} tone="purple" value="9" label="AI Recommendations" delta="3 pending review" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-1">
          <ProjectHealthCard />
        </div>
        <div className="xl:col-span-2">
          <ProgressOverviewCard />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <ActivityFeed />
        <RecommendationsPreview />
        <MilestonesPreview />
      </div>
    </div>
  )
}

export { DashboardPage }
