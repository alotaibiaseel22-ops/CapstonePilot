import { Menu, Bell, ChevronDown } from 'lucide-react'
import { Avatar } from '@/shared/components/ui/avatar'

function Topbar({ onMenuClick }) {
  return (
    <header className="flex h-[73px] shrink-0 items-center justify-between border-b border-border bg-white px-6">
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
        <button type="button" className="relative text-gray-500 hover:text-gray-700" aria-label="Notifications">
          <Bell className="size-5" />
          <span className="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-red-500" />
        </button>

        <button type="button" className="flex items-center gap-2">
          <Avatar initials="SA" />
          <span className="hidden text-left sm:block">
            <span className="block text-sm font-semibold leading-tight text-gray-900">Sarah Ahmed</span>
            <span className="block text-xs leading-tight text-muted-foreground">Supervisor</span>
          </span>
          <ChevronDown className="size-4 text-gray-400" />
        </button>
      </div>
    </header>
  )
}

export { Topbar }
