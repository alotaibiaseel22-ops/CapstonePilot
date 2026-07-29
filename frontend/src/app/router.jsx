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
import { ProjectScheduleGate } from '@/features/projects/components/ProjectScheduleGate'
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
          // Only the AI monitoring surfaces (Risk Analysis, Recommendations)
          // are gated on having a deadline - Share, Settings, and Plan
          // approval are core project usage, not "monitoring features," and
          // stay reachable immediately after creation. Dashboard metrics for
          // a no-deadline project degrade gracefully ("Deadline not set")
          // rather than being blocked (see ProjectCard.jsx).
          {
            element: <ProjectScheduleGate />,
            children: [
              { path: 'projects/:id/risks', element: <RisksPage /> },
              { path: 'projects/:id/recommendations', element: <RecommendationsPage /> },
            ],
          },
          { path: 'settings', element: <SettingsPage /> },
        ],
      },
    ],
  },
])

export { router }
