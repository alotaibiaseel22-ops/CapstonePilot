import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { CreateProjectPage } from '@/features/projects/pages/CreateProjectPage'
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
      { path: 'projects', element: <CreateProjectPage /> },
      { path: 'progress', element: <ProgressPage /> },
      { path: 'risks', element: <RisksPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
])

export { router }
