import { CheckCircle2, Circle, CircleDot, UserX } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { Avatar } from '@/shared/components/ui/avatar'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'
import { cn } from '@/shared/lib/utils'

const priorityTone = { high: 'destructive', medium: 'warning', low: 'default' }
const priorityLabel = { high: 'High', medium: 'Medium', low: 'Low' }

const statusMeta = {
  pending: { label: 'Pending', tone: 'default', color: 'gray', value: 0, icon: Circle },
  in_progress: { label: 'In Progress', tone: 'info', color: 'blue', value: 50, icon: CircleDot },
  done: { label: 'Done', tone: 'success', color: 'green', value: 100, icon: CheckCircle2 },
}

const NEXT_STATUS = { pending: 'in_progress', in_progress: 'done', done: 'pending' }

function initialsOf(name) {
  return (name ?? '')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

// Resolves who a task is assigned to (a real member/owner or a guest) from
// the two mutually-exclusive id fields TaskRead returns, against the
// members/guests lists already fetched for the picker below - TaskRead
// itself only ever returns ids, never a name.
function resolveAssignee(task, members, guests) {
  if (task.assignee_id) {
    const member = members.find((m) => m.user_id === task.assignee_id)
    return member ? { name: member.name, isGuest: false } : null
  }
  if (task.assignee_guest_id) {
    const guest = guests.find((g) => g.id === task.assignee_guest_id)
    return guest ? { name: guest.display_name, isGuest: true } : null
  }
  return null
}

function AssigneeMenu({ task, members, guests, onAssign, disabled }) {
  const assignee = resolveAssignee(task, members, guests)

  return (
    <DropdownMenu
      trigger={(triggerProps) => (
        <button
          type="button"
          aria-label={assignee ? `Reassign ${task.title}` : `Assign ${task.title}`}
          disabled={disabled}
          className="shrink-0 rounded-full disabled:opacity-50"
          {...triggerProps}
        >
          <Avatar
            initials={assignee ? initialsOf(assignee.name) : '+'}
            color={assignee?.isGuest ? 'navy' : 'blue'}
            className={cn(!assignee && 'bg-gray-200 text-gray-400')}
          />
        </button>
      )}
    >
      {members.map((member) => (
        <DropdownMenuItem
          key={member.user_id}
          onClick={() => onAssign({ assigneeId: member.user_id })}
        >
          {member.name}
          {member.role === 'owner' && <span className="text-muted-foreground"> (Owner)</span>}
        </DropdownMenuItem>
      ))}
      {guests.map((guest) => (
        <DropdownMenuItem key={guest.id} onClick={() => onAssign({ assigneeGuestId: guest.id })}>
          {guest.display_name} <span className="text-muted-foreground">(Guest)</span>
        </DropdownMenuItem>
      ))}
      {members.length === 0 && guests.length === 0 && (
        <p className="px-4 py-2 text-sm text-muted-foreground">No one to assign yet.</p>
      )}
      {assignee && (
        <DropdownMenuItem icon={UserX} destructive onClick={() => onAssign({})}>
          Unassign
        </DropdownMenuItem>
      )}
    </DropdownMenu>
  )
}

function TaskRow({ task, onStatusChange, updating, members = [], guests = [], onAssign }) {
  const meta = statusMeta[task.status]
  const StatusIcon = meta.icon
  const done = task.status === 'done'

  return (
    <div className="flex items-center gap-3 border-t border-border px-6 py-4">
      <button
        type="button"
        onClick={() => onStatusChange(NEXT_STATUS[task.status])}
        disabled={updating}
        aria-label={`Advance status for ${task.title}`}
        className="shrink-0 disabled:opacity-50"
      >
        <StatusIcon
          className={cn(
            'size-5',
            done ? 'text-green-600' : task.status === 'in_progress' ? 'text-blue-500' : 'text-gray-300',
          )}
        />
      </button>
      <p className={cn('flex-1 text-sm text-gray-800', done && 'text-muted-foreground line-through')}>
        {task.title}
      </p>
      {onAssign && (
        <AssigneeMenu
          task={task}
          members={members}
          guests={guests}
          onAssign={onAssign}
          disabled={updating}
        />
      )}
      <Badge variant={priorityTone[task.priority]}>{priorityLabel[task.priority]}</Badge>
      <Badge variant={meta.tone}>{meta.label}</Badge>
      <Progress value={meta.value} color={meta.color} className="w-24" />
      <span className="w-10 shrink-0 text-right text-sm text-muted-foreground">{meta.value}%</span>
    </div>
  )
}

export { TaskRow }
