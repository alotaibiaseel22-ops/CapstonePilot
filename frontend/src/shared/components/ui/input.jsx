import { cn } from '@/shared/lib/utils'

function Input({ className, icon: Icon, ...props }) {
  return (
    <div className="relative">
      {Icon && (
        <Icon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      )}
      <input
        className={cn(
          'h-11 w-full rounded-lg border border-border bg-gray-50 text-sm text-gray-900 placeholder:text-muted-foreground',
          'focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500',
          Icon ? 'pl-10 pr-3' : 'px-3',
          className,
        )}
        {...props}
      />
    </div>
  )
}

export { Input }
