import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'

function HealthGauge({ value = 0, max = 100 }) {
  return (
    <div className="relative flex size-56 items-center justify-center">
      <RadialBarChart
        width={224}
        height={224}
        cx="50%"
        cy="50%"
        innerRadius="78%"
        outerRadius="100%"
        barSize={16}
        data={[{ value }]}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, max]} tick={false} axisLine={false} />
        <RadialBar dataKey="value" cornerRadius={20} fill="#2563eb" background={{ fill: '#e5e7eb' }} />
      </RadialBarChart>
      <div className="absolute flex flex-col items-center">
        <span className="text-4xl font-bold text-gray-900">{value}</span>
        <span className="text-sm text-muted-foreground">/ {max}</span>
      </div>
    </div>
  )
}

export { HealthGauge }
