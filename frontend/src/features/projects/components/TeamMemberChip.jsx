import { X } from 'lucide-react'
import { Avatar } from '@/shared/components/ui/avatar'

function TeamMemberChip({ name, color, onRemove }) {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 py-1 pl-1.5 pr-3 text-sm font-medium text-blue-700">
      <Avatar initials={initials} color={color} className="size-6 text-[10px]" />
      {name}
      {onRemove && (
        <button type="button" onClick={onRemove} aria-label={`Remove ${name}`}>
          <X className="size-3.5 text-blue-400 hover:text-blue-600" />
        </button>
      )}
    </span>
  )
}

export { TeamMemberChip }
