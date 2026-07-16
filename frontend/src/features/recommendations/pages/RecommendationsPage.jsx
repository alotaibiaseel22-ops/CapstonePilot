import { PreviewDataBanner } from '@/shared/components/common/PreviewDataBanner'
import { AnalysisBanner } from '../components/AnalysisBanner'
import { RecommendationCard } from '../components/RecommendationCard'

const recommendations = [
  {
    title: 'Start unit testing immediately — do not wait for Phase 5',
    severity: 'Critical',
    category: 'Quality',
    effort: 'Medium',
    impact: 'High',
    description:
      'The current project plan delays all testing to Week 10. Writing tests now for completed modules will catch bugs early and save an estimated 12–18 hours of debugging later.',
    rationale:
      'AI analysis of similar capstone projects shows that teams that test-as-they-build have 40% fewer critical bugs at submission time.',
    defaultOpen: true,
  },
  {
    title: 'Redistribute backend tasks from Omar to Priya',
    severity: 'High',
    category: 'Team',
    effort: 'Low',
    impact: 'High',
    description:
      'Omar currently holds 7 of 14 open backend tasks. Transferring "API endpoint design" and "database indexing" to Priya will balance the workload and reduce single-point-of-failure risk.',
  },
  {
    title: 'Schedule a mid-sprint sync to address implementation delay',
    severity: 'High',
    category: 'Process',
    effort: 'Low',
    impact: 'Medium',
    description:
      'Implementation phase is 8 days behind the baseline schedule. A 30-minute team sync this week should identify blockers and produce a recovery plan before the delay compounds.',
  },
]

function RecommendationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
        <p className="mt-1 text-muted-foreground">AI-generated suggestions to improve project outcomes</p>
      </div>

      <PreviewDataBanner>
        Preview data — connects when Recommendation generation ships in Iteration 13.
      </PreviewDataBanner>

      <AnalysisBanner />

      <div className="space-y-4">
        {recommendations.map((rec) => (
          <RecommendationCard key={rec.title} {...rec} />
        ))}
      </div>
    </div>
  )
}

export { RecommendationsPage }
