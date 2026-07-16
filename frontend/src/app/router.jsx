import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { ProtectedRoute } from './layout/ProtectedRoute'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { RegisterPage } from '@/features/auth/pages/RegisterPage'
import { InviteAcceptPage } from '@/features/invitations/pages/InviteAcceptPage'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { ProjectListPage } from '@/features/projects/pages/ProjectListPage'
import { CreateProjectPage } from '@/features/projects/pages/CreateProjectPage'
import { ProjectDetailPage } from '@/features/projects/pages/ProjectDetailPage'
import { ProjectSettingsPage } from '@/features/projects/pages/ProjectSettingsPage'
import { ProgressPage } from '@/features/planning/pages/ProgressPage'
import { RisksPage } from '@/features/risks/pages/RisksPage'
import { RecommendationsPage } from '@/features/recommendations/pages/RecommendationsPage'
import { SettingsPage } from '@/features/settings/pages/SettingsPage'

const router = createBrowserRouter([
  { path: 'login', element: <LoginPage /> },
  { path: 'register', element: <RegisterPage /> },
  { path: 'invite/:token', element: <InviteAcceptPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: 'dashboard', element: <DashboardPage /> },
          { path: 'projects', element: <ProjectListPage /> },
          { path: 'projects/new', element: <CreateProjectPage /> },
          { path: 'projects/:id', element: <ProjectDetailPage /> },
          { path: 'projects/:id/settings', element: <ProjectSettingsPage /> },
          { path: 'projects/:id/progress', element: <ProgressPage /> },
          { path: 'risks', element: <RisksPage /> },
          { path: 'recommendations', element: <RecommendationsPage /> },
          { path: 'settings', element: <SettingsPage /> },
        ],
      },
    ],
  },
])

export { router }
