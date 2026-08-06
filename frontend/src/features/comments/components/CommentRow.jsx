import { Trash2 } from 'lucide-react'
import { Avatar } from '@/shared/components/ui/avatar'
import { formatRelativeTime } from '@/shared/lib/formatRelativeTime'

function initialsOf(name) {
  return (name ?? '')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

// Same "author is a User OR a Guest" resolution as TaskRow.jsx's
// resolveAssignee / AttachmentRow.jsx's resolveUploader.
function resolveAuthor(comment, members, guests) {
  if (comment.author_id) {
    const member = members.find((m) => m.user_id === comment.author_id)
    return member ? { name: member.name, isGuest: false } : null
  }
  if (comment.author_guest_id) {
    const guest = guests.find((g) => g.id === comment.author_guest_id)
    return guest ? { name: guest.display_name, isGuest: true } : null
  }
  return null
}

function CommentRow({
  comment,
  members = [],
  guests = [],
  currentUserId,
  currentGuestId,
  isProjectOwner,
  onDelete,
  deleting,
}) {
  const author = resolveAuthor(comment, members, guests)
  const isAuthor =
    (currentUserId && comment.author_id === currentUserId) ||
    (currentGuestId && comment.author_guest_id === currentGuestId)
  const canDelete = isAuthor || isProjectOwner

  return (
    <div className="flex gap-3 border-t border-border px-6 py-4">
      <Avatar
        initials={author ? initialsOf(author.name) : '?'}
        color={author?.isGuest ? 'navy' : 'blue'}
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-800">
            {author?.name ?? 'Unknown'}
            {author?.isGuest && <span className="font-normal text-muted-foreground"> (Guest)</span>}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatRelativeTime(comment.created_at)}
          </span>
        </div>
        <p className="mt-1 whitespace-pre-wrap text-sm text-gray-700">{comment.body}</p>
      </div>
      {canDelete && (
        <button
          type="button"
          aria-label="Delete comment"
          disabled={deleting}
          onClick={() => onDelete(comment.id)}
          className="shrink-0 self-start rounded-md p-1.5 text-gray-400 hover:bg-muted hover:text-red-600 disabled:opacity-50"
        >
          <Trash2 className="size-4" />
        </button>
      )}
    </div>
  )
}

export { CommentRow, resolveAuthor }
