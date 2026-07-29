import { ChevronDown, LayoutGrid } from 'lucide-react'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'

function ProjectFilterDropdown({ projects, selectedProjectId, onChange }) {
  const selected = projects.find((p) => p.id === selectedProjectId)
  const label = selected ? selected.name : 'All Projects'

  return (
    <DropdownMenu
      align="left"
      trigger={(triggerProps) => (
        <button
          type="button"
          className="flex items-center gap-2 rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-muted"
          {...triggerProps}
        >
          <LayoutGrid className="size-4 text-gray-500" />
          {label}
          <ChevronDown className="size-4 text-gray-400" />
        </button>
      )}
    >
      <DropdownMenuItem onClick={() => onChange(null)}>All Projects</DropdownMenuItem>
      {projects.map((project) => (
        <DropdownMenuItem key={project.id} onClick={() => onChange(project.id)}>
          {project.name}
        </DropdownMenuItem>
      ))}
    </DropdownMenu>
  )
}

export { ProjectFilterDropdown }
