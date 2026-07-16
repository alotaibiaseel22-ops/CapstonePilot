import { cn } from '@/shared/lib/utils'

function Textarea({ className, icon: Icon, ...props }) {
  return (
    <div className="relative">
      {Icon && <Icon className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />}
      <textarea
        className={cn(
          'min-h-28 w-full resize-none rounded-lg border border-border bg-gray-50 text-sm text-gray-900 placeholder:text-muted-foreground',
          'focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500',
          Icon ? 'pl-10 pr-3 py-3' : 'p-3',
          className,
        )}
        {...props}
      />
    </div>
  )
}

export { Textarea }
