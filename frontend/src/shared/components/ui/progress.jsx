import { cn } from '@/shared/lib/utils'

const barColors = {
  blue: 'bg-blue-600',
  green: 'bg-green-600',
  amber: 'bg-amber-500',
  red: 'bg-red-600',
  gray: 'bg-gray-300',
}

function Progress({ value = 0, color = 'blue', className, trackClassName }) {
  return (
    <div className={cn('h-1.5 w-full overflow-hidden rounded-full bg-gray-100', trackClassName)}>
      <div
        className={cn('h-full rounded-full transition-all', barColors[color] ?? barColors.blue, className)}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}

export { Progress }
