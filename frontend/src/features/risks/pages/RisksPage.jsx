import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { useProject } from '@/features/projects/hooks/useProjects'
import { useRisks } from '../hooks/useRisks'
import { RiskStatCard } from '../components/RiskStatCard'
import { FilterTabs } from '../components/FilterTabs'
import { RiskCard } from '../components/RiskCard'

function RisksPage() {
  const { id } = useParams()
  const [filter, setFilter] = useState('all')
  const { data: project, isLoading: projectLoading, isError: projectError } = useProject(id)
  const { data: risks, isLoading: risksLoading, isError: risksError } = useRisks(id)

  if (projectLoading || risksLoading) return <LoadingState label="Loading risks..." />
  if (projectError || risksError) {
    return <ErrorState message="Couldn't load risks for this project. Please try again." />
  }

  const counts = {
    all: risks.length,
    high: risks.filter((r) => r.severity === 'high').length,
    medium: risks.filter((r) => r.severity === 'medium').length,
    low: risks.filter((r) => r.severity === 'low').length,
  }
  const filterOptions = [
    { value: 'all', label: 'All', count: counts.all },
    { value: 'high', label: 'High', count: counts.high },
    { value: 'medium', label: 'Medium', count: counts.medium },
    { value: 'low', label: 'Low', count: counts.low },
  ]
  const visibleRisks = filter === 'all' ? risks : risks.filter((r) => r.severity === filter)

  return (
    <div className="space-y-6">
      <Link
        to={`/projects/${id}`}
        className="flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-gray-700"
      >
        <ArrowLeft className="size-4" />
        Back to project
      </Link>

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Risk Analysis</h1>
        <p className="mt-1 text-muted-foreground">AI-detected risks for {project.name}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <RiskStatCard value={counts.high} label="High Risk" tone="red" />
        <RiskStatCard value={counts.medium} label="Medium Risk" tone="amber" />
        <RiskStatCard value={counts.low} label="Low Risk" tone="green" />
      </div>

      <FilterTabs options={filterOptions} value={filter} onChange={setFilter} />

      {visibleRisks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center text-muted-foreground">
          {risks.length === 0
            ? 'No risks detected yet. CapstonePilot monitors this project automatically and will flag anything it finds here.'
            : 'No risks match this filter.'}
        </div>
      ) : (
        <div className="space-y-4">
          {visibleRisks.map((risk) => (
            <RiskCard key={risk.id} {...risk} />
          ))}
        </div>
      )}
    </div>
  )
}

export { RisksPage }
