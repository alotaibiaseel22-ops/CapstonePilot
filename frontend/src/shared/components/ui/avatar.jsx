import { cn } from '@/shared/lib/utils'

const avatarColors = {
  blue: 'bg-blue-600 text-white',
  navy: 'bg-blue-900 text-white',
}

function Avatar({ initials, color = 'blue', className }) {
  return (
    <span
      className={cn(
        'inline-flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold',
        avatarColors[color] ?? avatarColors.blue,
        className,
      )}
    >
      {initials}
    </span>
  )
}

export { Avatar }
