import { useMemo } from 'react'
import { useQueries } from '@tanstack/react-query'
import { useProjects } from '@/features/projects/hooks/useProjects'
import { getMilestones, getTasks } from '@/features/planning/api/milestones'
import { getRisks } from '@/features/risks/api/risks'
import { getRecommendations } from '@/features/recommendations/api/recommendations'

// Population standard deviation - mirrors the backend Decision Engine's own
// workload_imbalance formula (app/application/decision_engine/rules.py),
// computed here client-side since this hook already has the raw task list.
function populationStdDev(values) {
  if (values.length < 2) return 0
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length
  const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length
  return Math.sqrt(variance)
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

// Aggregates across every project the user owns/belongs to by default, or
// scopes to a single project when selectedProjectId is set - the Dashboard's
// "All Projects" vs per-project filter switches in place, no navigation.
function useDashboardData(selectedProjectId) {
  const { data: allProjects, isLoading: projectsLoading, isError: projectsError } = useProjects()

  const projects = useMemo(() => {
    if (!allProjects) return []
    return selectedProjectId ? allProjects.filter((p) => p.id === selectedProjectId) : allProjects
  }, [allProjects, selectedProjectId])

  const milestoneQueries = useQueries({
    queries: projects.map((p) => ({
      queryKey: ['projects', p.id, 'milestones'],
      queryFn: () => getMilestones(p.id),
    })),
  })
  const riskQueries = useQueries({
    queries: projects.map((p) => ({
      queryKey: ['projects', p.id, 'risks'],
      queryFn: () => getRisks(p.id),
    })),
  })
  const recommendationQueries = useQueries({
    queries: projects.map((p) => ({
      queryKey: ['projects', p.id, 'recommendations'],
      queryFn: () => getRecommendations(p.id),
    })),
  })

  const allMilestones = milestoneQueries.flatMap((q) => q.data ?? [])
  const taskQueries = useQueries({
    queries: allMilestones.map((m) => ({
      queryKey: ['milestones', m.id, 'tasks'],
      queryFn: () => getTasks(m.id),
    })),
  })
  const allTasks = taskQueries.flatMap((q) => q.data ?? [])

  const isLoading =
    projectsLoading ||
    milestoneQueries.some((q) => q.isLoading) ||
    taskQueries.some((q) => q.isLoading) ||
    riskQueries.some((q) => q.isLoading) ||
    recommendationQueries.some((q) => q.isLoading)
  const isError =
    projectsError ||
    milestoneQueries.some((q) => q.isError) ||
    taskQueries.some((q) => q.isError) ||
    riskQueries.some((q) => q.isError) ||
    recommendationQueries.some((q) => q.isError)

  const allRisks = riskQueries.flatMap((q) => q.data ?? [])
  const allRecommendations = recommendationQueries.flatMap((q) => q.data ?? [])

  const totalTasks = allTasks.length
  const doneTasks = allTasks.filter((t) => t.status === 'done').length
  const progressPercent = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0

  const risksBySeverity = {
    high: allRisks.filter((r) => r.severity === 'high').length,
    medium: allRisks.filter((r) => r.severity === 'medium').length,
    low: allRisks.filter((r) => r.severity === 'low').length,
  }
  const pendingRecommendations = allRecommendations.filter((r) => r.status === 'pending')

  // Real "Overall Project Health" (replaces the old hardcoded ProjectHealthCard
  // numbers) - derived entirely from data already fetched above, no extra
  // backend call. Schedule adherence and workload balance mirror the backend
  // Decision Engine's own overdue_ratio/workload_imbalance formulas.
  const today = new Date()
  const overdueTasks = allTasks.filter(
    (t) => t.status !== 'done' && t.due_date && new Date(t.due_date) < today,
  ).length
  const overdueRatio = totalTasks > 0 ? overdueTasks / totalTasks : 0
  const scheduleAdherence = Math.round(clamp(100 - overdueRatio * 100, 0, 100))

  const openTaskCountsByAssignee = {}
  for (const t of allTasks) {
    if (t.assignee_id && t.status !== 'done') {
      openTaskCountsByAssignee[t.assignee_id] = (openTaskCountsByAssignee[t.assignee_id] ?? 0) + 1
    }
  }
  const workloadStdDev = populationStdDev(Object.values(openTaskCountsByAssignee))
  const workloadBalance = Math.round(clamp(100 - workloadStdDev * 25, 0, 100))

  const riskLevel = Math.round(
    clamp(risksBySeverity.high * 20 + risksBySeverity.medium * 10 + risksBySeverity.low * 5, 0, 100),
  )
  const overallHealth = Math.round(
    clamp((scheduleAdherence + workloadBalance + (100 - riskLevel)) / 3, 0, 100),
  )
  const healthLabel = overallHealth >= 70 ? 'Good' : overallHealth >= 40 ? 'Fair' : 'Poor'
  const healthBadgeVariant =
    overallHealth >= 70 ? 'success' : overallHealth >= 40 ? 'warning' : 'destructive'

  const upcomingMilestones = allMilestones
    .filter((m) => m.due_date)
    .map((m) => {
      const tasksForMilestone = allTasks.filter((t) => t.milestone_id === m.id)
      const total = tasksForMilestone.length
      const done = tasksForMilestone.filter((t) => t.status === 'done').length
      const value = total > 0 ? Math.round((done / total) * 100) : 0
      return { ...m, value, done: value === 100 }
    })
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
    .slice(0, 5)

  return {
    isLoading,
    isError,
    projects,
    progressPercent,
    totalTasks,
    doneTasks,
    risks: allRisks,
    risksBySeverity,
    recommendations: allRecommendations,
    pendingRecommendations,
    upcomingMilestones,
    health: {
      overallHealth,
      healthLabel,
      healthBadgeVariant,
      scheduleAdherence,
      workloadBalance,
      riskLevel,
    },
  }
}

export { useDashboardData }
