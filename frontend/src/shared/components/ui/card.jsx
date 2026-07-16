import { cn } from '@/shared/lib/utils'

function Card({ className, ...props }) {
  return (
    <div className={cn('rounded-xl border border-border bg-white', className)} {...props} />
  )
}

function CardHeader({ className, ...props }) {
  return <div className={cn('flex items-center justify-between p-6 pb-0', className)} {...props} />
}

function CardTitle({ className, ...props }) {
  return <h3 className={cn('text-base font-bold text-gray-900', className)} {...props} />
}

function CardDescription({ className, ...props }) {
  return <p className={cn('text-sm text-muted-foreground', className)} {...props} />
}

function CardContent({ className, ...props }) {
  return <div className={cn('p-6', className)} {...props} />
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent }
