import { Card, CardContent } from '@/shared/components/ui/card'
import { cn } from '@/shared/lib/utils'

const tones = {
  blue: 'bg-blue-100 text-blue-600',
  green: 'bg-green-100 text-green-600',
  amber: 'bg-amber-100 text-amber-600',
  purple: 'bg-purple-100 text-purple-600',
}

const deltaTones = {
  green: 'text-green-600',
  amber: 'text-amber-600',
}

function StatCard({ icon: Icon, tone = 'blue', value, label, delta, deltaTone = 'green' }) {
  return (
    <Card>
      <CardContent>
        <span className={cn('flex size-12 items-center justify-center rounded-xl', tones[tone])}>
          <Icon className="size-6" />
        </span>
        <p className="mt-4 text-3xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
        {delta && <p className={cn('mt-2 text-sm font-medium', deltaTones[deltaTone])}>{delta}</p>}
      </CardContent>
    </Card>
  )
}

export { StatCard }
