import { useState } from 'react'
import { TrendingUp, CircleCheck, TriangleAlert, Lightbulb } from 'lucide-react'
import { StatCard } from '@/shared/components/common/StatCard'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { ProjectFilterDropdown } from '../components/ProjectFilterDropdown'
import { ProjectHealthCard } from '../components/ProjectHealthCard'
import { ProgressOverviewCard } from '../components/ProgressOverviewCard'
import { ActivityFeed } from '../components/ActivityFeed'
import { RecommendationsPreview } from '../components/RecommendationsPreview'
import { MilestonesPreview } from '../components/MilestonesPreview'
import { useDashboardData } from '../hooks/useDashboardData'

function DashboardPage() {
  const [selectedProjectId, setSelectedProjectId] = useState(null)
  const dashboard = useDashboardData(selectedProjectId)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-muted-foreground">
            CapstonePilot automatically monitors your projects for risks and recommendations.
          </p>
        </div>
        <ProjectFilterDropdown
          projects={dashboard.projects.length ? dashboard.projects : []}
          selectedProjectId={selectedProjectId}
          onChange={setSelectedProjectId}
        />
      </div>

      {dashboard.isLoading ? (
        <LoadingState label="Loading dashboard..." />
      ) : dashboard.isError ? (
        <ErrorState message="Couldn't load dashboard data. Please try again." />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              icon={TrendingUp}
              tone="blue"
              value={`${dashboard.progressPercent}%`}
              label="Project Progress"
            />
            <StatCard
              icon={CircleCheck}
              tone="green"
              value={dashboard.doneTasks}
              label="Completed Tasks"
            />
            <StatCard
              icon={TriangleAlert}
              tone="amber"
              value={dashboard.risks.length}
              label="Detected Risks"
              delta={
                dashboard.risksBySeverity.high > 0
                  ? `${dashboard.risksBySeverity.high} high severity`
                  : undefined
              }
              deltaTone="amber"
            />
            <StatCard
              icon={Lightbulb}
              tone="purple"
              value={dashboard.recommendations.length}
              label="AI Recommendations"
              delta={
                dashboard.pendingRecommendations.length > 0
                  ? `${dashboard.pendingRecommendations.length} pending review`
                  : undefined
              }
            />
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="xl:col-span-1">
              <ProjectHealthCard {...dashboard.health} />
            </div>
            <div className="xl:col-span-2">
              <ProgressOverviewCard />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <ActivityFeed />
            <RecommendationsPreview recommendations={dashboard.pendingRecommendations} />
            <MilestonesPreview milestones={dashboard.upcomingMilestones} />
          </div>
        </>
      )}
    </div>
  )
}

export { DashboardPage }
