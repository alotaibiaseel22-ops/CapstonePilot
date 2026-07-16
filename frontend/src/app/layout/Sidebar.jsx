import { NavLink } from 'react-router-dom'
import {
  LayoutGrid,
  Folder,
  TrendingUp,
  TriangleAlert,
  Lightbulb,
  Settings,
  Cpu,
} from 'lucide-react'
import { cn } from '@/shared/lib/utils'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutGrid },
  { to: '/projects', label: 'Projects', icon: Folder },
  { to: '/progress', label: 'Progress', icon: TrendingUp },
  { to: '/risks', label: 'Risks', icon: TriangleAlert },
  { to: '/recommendations', label: 'Recommendations', icon: Lightbulb },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function Sidebar({ open, onNavigate }) {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex w-[280px] shrink-0 -translate-x-full flex-col border-r border-border bg-white transition-transform duration-200 md:static md:translate-x-0',
        open && 'translate-x-0',
      )}
    >
      <div className="flex items-center gap-3 border-b border-border p-6">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-600">
          <Cpu className="size-5 text-white" />
        </span>
        <div>
          <p className="text-base font-bold leading-tight text-gray-900">CapstonePilot</p>
          <p className="text-xs text-muted-foreground">AI Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-gray-700 hover:bg-muted',
                isActive && 'bg-blue-50 text-blue-600 hover:bg-blue-50',
              )
            }
          >
            <Icon className="size-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="m-4 rounded-xl bg-blue-50 p-4">
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-green-500" />
          <p className="text-sm font-semibold text-gray-900">AI Agent Active</p>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">Monitoring 3 projects &middot; Last scan 2m ago</p>
      </div>
    </aside>
  )
}

export { Sidebar }
