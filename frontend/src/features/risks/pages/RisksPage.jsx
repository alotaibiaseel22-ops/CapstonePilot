import { useState } from 'react'
import { PreviewDataBanner } from '@/shared/components/common/PreviewDataBanner'
import { RiskStatCard } from '../components/RiskStatCard'
import { FilterTabs } from '../components/FilterTabs'
import { RiskCard } from '../components/RiskCard'

const risks = [
  {
    title: 'Implementation phase behind schedule',
    severity: 'High',
    category: 'Schedule',
    date: 'Jul 9, 2026 · 09:14 AM',
    description:
      'Three backend tasks are overdue by an average of 4 days. The LSTM model integration was originally due July 28 and has not started.',
  },
  {
    title: 'Testing started too late in the timeline',
    severity: 'High',
    category: 'Quality',
    date: 'Jul 7, 2026 · 04:30 PM',
    description:
      'Testing is currently planned exclusively for Phase 5 (Week 10+). No unit or integration tests have been written for any completed modules.',
  },
  {
    title: 'Unequal workload distribution',
    severity: 'Medium',
    category: 'Team',
    date: 'Jul 8, 2026 · 11:00 AM',
    description:
      'Omar Al-Rashidi has 7 open tasks, Priya Nair has 2, and Lena Fischer has 1. This creates a bottleneck risk and a single point of failure.',
  },
  {
    title: 'Dataset quality concerns',
    severity: 'Medium',
    category: 'Technical',
    date: 'Jul 5, 2026 · 02:45 PM',
    description:
      'The primary traffic dataset has 14% missing values in peak-hour readings and an inconsistent sampling rate between sensor nodes.',
  },
  {
    title: 'Frontend integration not yet started',
    severity: 'Medium',
    category: 'Schedule',
    date: 'Jul 9, 2026 · 08:00 AM',
    description:
      'React dashboard components have not begun development. Frontend is currently only at wireframe stage with a Aug 16 deadline.',
  },
  {
    title: 'No version control branching strategy defined',
    severity: 'Low',
    category: 'Process',
    date: 'Jul 6, 2026 · 10:20 AM',
    description:
      'All team members are committing directly to the main branch. There are no code review requirements or pull request workflows in place.',
  },
]

const counts = {
  All: risks.length,
  High: risks.filter((r) => r.severity === 'High').length,
  Medium: risks.filter((r) => r.severity === 'Medium').length,
  Low: risks.filter((r) => r.severity === 'Low').length,
}

const filterOptions = [
  { value: 'All', label: 'All', count: counts.All },
  { value: 'High', label: 'High', count: counts.High },
  { value: 'Medium', label: 'Medium', count: counts.Medium },
  { value: 'Low', label: 'Low', count: counts.Low },
]

function RisksPage() {
  const [filter, setFilter] = useState('All')
  const visibleRisks = filter === 'All' ? risks : risks.filter((r) => r.severity === filter)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Risk Analysis</h1>
        <p className="mt-1 text-muted-foreground">AI-detected risks across all monitored projects</p>
      </div>

      <PreviewDataBanner>
        Preview data — connects when Risk Analysis ships in Iteration 12.
      </PreviewDataBanner>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <RiskStatCard value={counts.High} label="High Risk" tone="red" />
        <RiskStatCard value={counts.Medium} label="Medium Risk" tone="amber" />
        <RiskStatCard value={counts.Low} label="Low Risk" tone="green" />
      </div>

      <FilterTabs options={filterOptions} value={filter} onChange={setFilter} />

      <div className="space-y-4">
        {visibleRisks.map((risk) => (
          <RiskCard key={risk.title} {...risk} />
        ))}
      </div>
    </div>
  )
}

export { RisksPage }
