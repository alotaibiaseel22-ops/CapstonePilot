import { Modal } from '@/shared/components/ui/modal'
import { Badge } from '@/shared/components/ui/badge'
import { Avatar } from '@/shared/components/ui/avatar'

function initialsOf(text) {
  return text
    .split(/[\s@.]+/)
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function formatDate(value) {
  return new Date(value).toLocaleDateString(undefined, {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

function ProfileModal({ profile, onClose }) {
  return (
    <Modal open={Boolean(profile)} onClose={onClose} title="Profile" className="max-w-sm">
      {profile && (
        <div className="flex flex-col items-center gap-3 py-2 text-center">
          <Avatar initials={initialsOf(profile.name || profile.email)} className="size-16 text-lg" />
          <div>
            <p className="text-lg font-semibold text-gray-900">{profile.name || profile.email}</p>
            <p className="text-sm text-muted-foreground">{profile.email}</p>
          </div>
          <Badge variant={profile.badgeVariant}>{profile.badge}</Badge>
          {profile.joinedAt && (
            <p className="text-xs text-muted-foreground">Joined {formatDate(profile.joinedAt)}</p>
          )}
        </div>
      )}
    </Modal>
  )
}

export { ProfileModal }
