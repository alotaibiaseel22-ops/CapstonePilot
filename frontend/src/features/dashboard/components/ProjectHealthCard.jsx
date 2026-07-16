import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { HealthGauge } from './HealthGauge'

const metrics = [
  { label: 'Schedule adherence', value: 78, color: 'green' },
  { label: 'Team collaboration', value: 88, color: 'green' },
  { label: 'Risk level', value: 62, color: 'amber' },
]

function ProjectHealthCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Health</CardTitle>
        <Badge variant="success">Good</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex justify-center">
          <HealthGauge value={72} />
        </div>
        <div className="mt-6 space-y-4">
          {metrics.map(({ label, value, color }) => (
            <div key={label}>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-gray-700">{label}</span>
                <span className="font-semibold text-gray-900">{value}%</span>
              </div>
              <Progress value={value} color={color} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export { ProjectHealthCard }
