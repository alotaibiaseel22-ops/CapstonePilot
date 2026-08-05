import { Outlet } from 'react-router-dom'
import { useGuestSession } from '@/app/providers/GuestSessionProvider'
import { GuestJoinForm } from '@/features/guest/components/GuestJoinForm'

// Guest-only analogue of ProtectedRoute.jsx: instead of redirecting
// somewhere else when there's no session, it renders the join form
// in place - a shareable link has nowhere else to send an unjoined
// visitor.
function GuestRoute() {
  const { status } = useGuestSession()

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 text-muted-foreground">
        Loading...
      </div>
    )
  }

  if (status === 'needs-join') {
    return <GuestJoinForm />
  }

  return <Outlet />
}

export { GuestRoute }
