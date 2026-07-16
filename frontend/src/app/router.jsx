import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { ProjectListPage } from '@/features/projects/pages/ProjectListPage'
import { CreateProjectPage } from '@/features/projects/pages/CreateProjectPage'
import { ProjectDetailPage } from '@/features/projects/pages/ProjectDetailPage'
import { ProgressPage } from '@/features/planning/pages/ProgressPage'
import { RisksPage } from '@/features/risks/pages/RisksPage'
import { RecommendationsPage } from '@/features/recommendations/pages/RecommendationsPage'
import { SettingsPage } from '@/features/settings/pages/SettingsPage'

const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'projects', element: <ProjectListPage /> },
      { path: 'projects/new', element: <CreateProjectPage /> },
      { path: 'projects/:id', element: <ProjectDetailPage /> },
      { path: 'progress', element: <ProgressPage /> },
      { path: 'risks', element: <RisksPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
])

export { router }
