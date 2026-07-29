import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { useProject } from '@/features/projects/hooks/useProjects'
import { useRecommendations } from '../hooks/useRecommendations'
import { AnalysisBanner } from '../components/AnalysisBanner'
import { RecommendationCard } from '../components/RecommendationCard'

function RecommendationsPage() {
  const { id } = useParams()
  const { data: project, isLoading: projectLoading, isError: projectError } = useProject(id)
  const {
    data: recommendations,
    isLoading: recsLoading,
    isError: recsError,
  } = useRecommendations(id)

  if (projectLoading || recsLoading) return <LoadingState label="Loading recommendations..." />
  if (projectError || recsError) {
    return <ErrorState message="Couldn't load recommendations for this project. Please try again." />
  }

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
        <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
        <p className="mt-1 text-muted-foreground">AI-generated suggestions for {project.name}</p>
      </div>

      {recommendations.length > 0 && <AnalysisBanner />}

      {recommendations.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center text-muted-foreground">
          No recommendations yet. CapstonePilot monitors this project automatically and will
          suggest improvements here.
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <RecommendationCard key={rec.id} projectId={id} {...rec} />
          ))}
        </div>
      )}
    </div>
  )
}

export { RecommendationsPage }
