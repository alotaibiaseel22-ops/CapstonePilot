import { useQueries, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useProjects } from '@/features/projects/hooks/useProjects'
import { getActivity, getUnreadCount, markSeen } from '../api/activity'

// Fans out across the user's own projects, same shape as the Dashboard's
// existing risks/recommendations/milestones fan-outs - kept standalone
// (rather than folded into useDashboardData) since the Topbar renders this
// on every page, not just the Dashboard.
function useActivity(limit = 10) {
  const { data: projects } = useProjects()

  const queries = useQueries({
    queries: (projects ?? []).map((p) => ({
      queryKey: ['projects', p.id, 'activity'],
      queryFn: ({ signal }) => getActivity(p.id, signal),
      enabled: Boolean(projects),
    })),
  })

  const isLoading = !projects || queries.some((q) => q.isLoading)
  const events = queries
    .flatMap((q) => q.data ?? [])
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, limit)

  return { data: events, isLoading }
}

function useUnreadCount() {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: ({ signal }) => getUnreadCount(signal),
    refetchInterval: 60_000,
  })
}

function useMarkSeen() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: markSeen,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] })
    },
  })
}

export { useActivity, useUnreadCount, useMarkSeen }
