import { useState } from 'react'
import { Menu, Bell, ChevronDown, LogOut } from 'lucide-react'
import { Avatar } from '@/shared/components/ui/avatar'
import { useAuth } from '@/app/providers/AuthProvider'
import { useActivity, useUnreadCount, useMarkSeen } from '@/features/activity/hooks/useActivity'

const roleLabels = {
  project_owner: 'Project Owner',
  collaborator: 'Collaborator',
}

function initialsOf(name) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function Topbar({ onMenuClick }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const { data: recentActivity = [] } = useActivity(6)
  const { data: unread } = useUnreadCount()
  const markSeen = useMarkSeen()

  function toggleNotifications() {
    setNotificationsOpen((open) => {
      const next = !open
      if (next && unread?.count > 0) {
        markSeen.mutate()
      }
      return next
    })
  }

  return (
    <header className="relative flex h-[73px] shrink-0 items-center justify-between border-b border-border bg-white px-6">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onMenuClick}
          className="text-gray-500 hover:text-gray-700"
          aria-label="Toggle sidebar"
        >
          <Menu className="size-5" />
        </button>
        <span className="hidden h-5 w-px bg-border sm:block" />
        <p className="hidden text-sm text-gray-600 sm:block">Spring 2026 Semester</p>
      </div>

      <div className="flex items-center gap-5">
        <div className="relative">
          <button
            type="button"
            onClick={toggleNotifications}
            className="relative text-gray-500 hover:text-gray-700"
            aria-label="Notifications"
          >
            <Bell className="size-5" />
            {unread?.count > 0 && (
              <span className="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-red-500" />
            )}
          </button>

          {notificationsOpen && (
            <>
              <button
                type="button"
                aria-label="Close notifications"
                className="fixed inset-0 z-40 cursor-default"
                onClick={() => setNotificationsOpen(false)}
              />
              <div className="absolute right-0 top-12 z-50 w-80 rounded-lg border border-border bg-white py-2 shadow-md">
                <p className="px-4 pb-2 text-xs font-semibold tracking-wide text-gray-500">
                  RECENT ACTIVITY
                </p>
                {recentActivity.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-muted-foreground">No activity yet.</p>
                ) : (
                  recentActivity.map((event) => (
                    <div key={event.id} className="px-4 py-2 text-sm text-gray-700">
                      {event.message}
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex items-center gap-2"
          >
            <Avatar initials={user ? initialsOf(user.name) : ''} />
            <span className="hidden text-left sm:block">
              <span className="block text-sm font-semibold leading-tight text-gray-900">
                {user?.name}
              </span>
              <span className="block text-xs leading-tight text-muted-foreground">
                {roleLabels[user?.role] ?? user?.role}
              </span>
            </span>
            <ChevronDown className="size-4 text-gray-400" />
          </button>

          {menuOpen && (
            <>
              <button
                type="button"
                aria-label="Close menu"
                className="fixed inset-0 z-40 cursor-default"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 top-12 z-50 w-44 rounded-lg border border-border bg-white py-1 shadow-md">
                <button
                  type="button"
                  onClick={logout}
                  className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-muted"
                >
                  <LogOut className="size-4" />
                  Log out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

export { Topbar }
