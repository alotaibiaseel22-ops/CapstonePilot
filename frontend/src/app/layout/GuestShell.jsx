import { Outlet } from 'react-router-dom'
import { Cpu, User } from 'lucide-react'
import { useGuestSession } from '@/app/providers/GuestSessionProvider'

// Deliberately minimal, and deliberately NOT AppShell with role checks
// bolted on: no Sidebar (no project switcher, no "New Project", no
// Settings, no Share/Invite UI) - a guest never has those actions, so this
// shell simply never renders the affordances for them.
function GuestShell() {
  const { session } = useGuestSession()

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="flex h-[73px] shrink-0 items-center justify-between border-b border-border bg-white px-6">
        <div className="flex items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-600">
            <Cpu className="size-5 text-white" />
          </span>
          <div>
            <p className="text-sm font-bold leading-tight text-gray-900">CapstonePilot</p>
            <p className="text-xs text-muted-foreground">Guest view</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <User className="size-4 text-gray-400" />
          {session?.guest?.display_name}
        </div>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}

export { GuestShell }
