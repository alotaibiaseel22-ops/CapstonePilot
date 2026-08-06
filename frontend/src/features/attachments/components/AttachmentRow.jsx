import { Download, Paperclip, Trash2 } from 'lucide-react'
import { Avatar } from '@/shared/components/ui/avatar'
import { DropdownMenu, DropdownMenuItem } from '@/shared/components/ui/dropdown-menu'
import { formatRelativeTime } from '@/shared/lib/formatRelativeTime'

function initialsOf(name) {
  return (name ?? '')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Resolves who uploaded a file from the two mutually-exclusive id fields
// AttachmentRead returns, against the members/guests lists already fetched
// for this project - structurally identical to TaskRow.jsx's
// resolveAssignee, since it's the same "author is a User OR a Guest" shape.
function resolveUploader(attachment, members, guests) {
  if (attachment.uploader_id) {
    const member = members.find((m) => m.user_id === attachment.uploader_id)
    return member ? { name: member.name, isGuest: false } : null
  }
  if (attachment.uploader_guest_id) {
    const guest = guests.find((g) => g.id === attachment.uploader_guest_id)
    return guest ? { name: guest.display_name, isGuest: true } : null
  }
  return null
}

function AttachmentRow({
  attachment,
  members = [],
  guests = [],
  currentUserId,
  currentGuestId,
  isProjectOwner,
  onDownload,
  onDelete,
  deleting,
}) {
  const uploader = resolveUploader(attachment, members, guests)
  const isAuthor =
    (currentUserId && attachment.uploader_id === currentUserId) ||
    (currentGuestId && attachment.uploader_guest_id === currentGuestId)
  const canDelete = isAuthor || isProjectOwner

  return (
    <div className="flex items-center gap-3 border-t border-border px-6 py-4">
      <Paperclip className="size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-800">{attachment.filename}</p>
        <p className="text-xs text-muted-foreground">
          {formatBytes(attachment.size_bytes)} &middot; {formatRelativeTime(attachment.created_at)}
        </p>
      </div>
      {uploader && (
        <div className="flex shrink-0 items-center gap-2">
          <Avatar initials={initialsOf(uploader.name)} color={uploader.isGuest ? 'navy' : 'blue'} />
          <span className="hidden text-sm text-muted-foreground sm:inline">
            {uploader.name}
            {uploader.isGuest && <span className="text-muted-foreground"> (Guest)</span>}
          </span>
        </div>
      )}
      <button
        type="button"
        aria-label={`Download ${attachment.filename}`}
        onClick={() => onDownload(attachment)}
        className="shrink-0 rounded-md p-1.5 text-gray-400 hover:bg-muted hover:text-gray-700"
      >
        <Download className="size-4" />
      </button>
      {canDelete && (
        <DropdownMenu
          trigger={(triggerProps) => (
            <button
              type="button"
              aria-label={`Actions for ${attachment.filename}`}
              className="shrink-0 rounded-md p-1.5 text-gray-400 hover:bg-muted hover:text-gray-700"
              {...triggerProps}
            >
              <Trash2 className="size-4" />
            </button>
          )}
        >
          <DropdownMenuItem
            icon={Trash2}
            destructive
            disabled={deleting}
            onClick={() => onDelete(attachment.id)}
          >
            Delete
          </DropdownMenuItem>
        </DropdownMenu>
      )}
    </div>
  )
}

export { AttachmentRow, formatBytes, resolveUploader }
