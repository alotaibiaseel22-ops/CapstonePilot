import { Card, CardContent } from '@/shared/components/ui/card'
import { cn } from '@/shared/lib/utils'

const tones = {
  red: 'text-red-600',
  amber: 'text-amber-600',
  green: 'text-green-600',
}

function RiskStatCard({ value, label, tone = 'red' }) {
  return (
    <Card>
      <CardContent>
        <p className={cn('text-3xl font-bold', tones[tone])}>{value}</p>
        <p className={cn('mt-1 text-sm font-medium', tones[tone])}>{label}</p>
      </CardContent>
    </Card>
  )
}

export { RiskStatCard }
