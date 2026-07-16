import { MilestoneAccordion } from '../components/MilestoneAccordion'

const milestones = [
  {
    title: 'Requirements & Research',
    status: 'Complete',
    value: 100,
    dueDate: 'Jul 19, 2026',
    tasks: [
      { title: 'Gather stakeholder requirements', priority: 'High', status: 'Done', value: 100 },
      { title: 'Literature review on traffic prediction models', priority: 'Medium', status: 'Done', value: 100 },
      { title: 'Define success metrics', priority: 'Medium', status: 'Done', value: 100 },
      { title: 'Finalize project scope document', priority: 'High', status: 'Done', value: 100 },
    ],
  },
  {
    title: 'Data Pipeline & Preprocessing',
    value: 72,
    dueDate: 'Aug 2, 2026',
    defaultOpen: true,
    tasks: [
      { title: 'Collect traffic sensor data', priority: 'High', status: 'Done', value: 100 },
      { title: 'Clean and normalize dataset', priority: 'High', status: 'In Progress', value: 80 },
      { title: 'Feature engineering', priority: 'Medium', status: 'In Progress', value: 55 },
      { title: 'Train/test split and validation strategy', priority: 'Medium', status: 'Pending', value: 0 },
    ],
  },
  {
    title: 'Model Development',
    value: 38,
    dueDate: 'Aug 23, 2026',
    defaultOpen: true,
    tasks: [
      { title: 'Implement LSTM baseline model', priority: 'High', status: 'In Progress', value: 65 },
      { title: 'Hyperparameter tuning', priority: 'Medium', status: 'Pending', value: 0 },
      { title: 'Model evaluation and benchmarking', priority: 'High', status: 'Pending', value: 0 },
      { title: 'Integrate real-time prediction API', priority: 'High', status: 'Pending', value: 0 },
    ],
  },
  {
    title: 'Dashboard & Frontend',
    value: 12,
    dueDate: 'Sep 13, 2026',
    defaultOpen: true,
    tasks: [
      { title: 'Design UI wireframes', priority: 'Medium', status: 'Done', value: 100 },
      { title: 'Build React dashboard components', priority: 'High', status: 'In Progress', value: 20 },
      { title: 'Integrate map visualization', priority: 'Medium', status: 'Pending', value: 0 },
      { title: 'Connect to backend API', priority: 'High', status: 'Pending', value: 0 },
    ],
  },
  {
    title: 'Testing & Deployment',
    value: 0,
    dueDate: 'Oct 1, 2026',
    tasks: [
      { title: 'Write unit and integration test plan', priority: 'High', status: 'Pending', value: 0 },
      { title: 'Set up CI pipeline', priority: 'Medium', status: 'Pending', value: 0 },
      { title: 'User acceptance testing', priority: 'Medium', status: 'Pending', value: 0 },
      { title: 'Deploy to production', priority: 'High', status: 'Pending', value: 0 },
    ],
  },
]

function ProgressPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Project Plan</h1>
          <p className="mt-1 text-muted-foreground">ML-Based Traffic Optimization &middot; 5 milestones &middot; 20 tasks</p>
        </div>
        <span className="rounded-full border border-border bg-white px-4 py-2 text-sm">
          Overall <span className="font-bold text-blue-600">44%</span>
        </span>
      </div>

      <div className="space-y-4">
        {milestones.map((m) => (
          <MilestoneAccordion key={m.title} {...m} />
        ))}
      </div>
    </div>
  )
}

export { ProgressPage }
