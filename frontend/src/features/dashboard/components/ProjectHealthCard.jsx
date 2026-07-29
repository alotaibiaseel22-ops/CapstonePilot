import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { HealthGauge } from './HealthGauge'

// scheduleAdherence/workloadBalance: higher is better. riskLevel: higher is
// worse (a raw risk score, matching the Dashboard stat card's semantics) -
// its bar color logic is deliberately inverted from the other two.
function toneFor(value, { inverted = false } = {}) {
  const score = inverted ? 100 - value : value
  if (score >= 70) return 'green'
  if (score >= 40) return 'amber'
  return 'red'
}

function ProjectHealthCard({
  overallHealth = 0,
  healthLabel = 'Good',
  healthBadgeVariant = 'success',
  scheduleAdherence = 0,
  workloadBalance = 0,
  riskLevel = 0,
}) {
  const metrics = [
    { label: 'Schedule adherence', value: scheduleAdherence, color: toneFor(scheduleAdherence) },
    { label: 'Workload balance', value: workloadBalance, color: toneFor(workloadBalance) },
    { label: 'Risk level', value: riskLevel, color: toneFor(riskLevel, { inverted: true }) },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Health</CardTitle>
        <Badge variant={healthBadgeVariant}>{healthLabel}</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex justify-center">
          <HealthGauge value={overallHealth} />
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
