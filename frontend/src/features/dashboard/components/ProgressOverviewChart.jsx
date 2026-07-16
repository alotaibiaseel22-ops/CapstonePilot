import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts'

const data = [
  { week: 'W1', completion: 5 },
  { week: 'W2', completion: 20 },
  { week: 'W3', completion: 24 },
  { week: 'W4', completion: 38 },
  { week: 'W5', completion: 50 },
  { week: 'W6', completion: 62 },
  { week: 'W7', completion: 64 },
  { week: 'W8', completion: 70 },
]

function ProgressOverviewChart() {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="completionFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
        <XAxis dataKey="week" tickLine={false} axisLine={false} tick={{ fill: '#9ca3af', fontSize: 12 }} />
        <YAxis
          domain={[0, 100]}
          ticks={[0, 25, 50, 75, 100]}
          tickLine={false}
          axisLine={false}
          tick={{ fill: '#9ca3af', fontSize: 12 }}
        />
        <Area
          type="monotone"
          dataKey="completion"
          stroke="#2563eb"
          strokeWidth={2}
          fill="url(#completionFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export { ProgressOverviewChart }
