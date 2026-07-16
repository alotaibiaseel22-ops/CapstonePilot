const projects = [
  {
    id: 'ml-traffic-optimization',
    name: 'ML-Based Traffic Optimization',
    description:
      'A machine learning system that analyzes real-time traffic data to optimize signal timing and reduce congestion in urban intersections. The system will use LSTM neural networks for prediction and a React-based dashboard for monitoring.',
    status: 'Active',
    health: 'At Risk',
    progress: 44,
    startDate: '2026-07-15',
    dueDate: '2026-12-01',
    team: [
      { name: 'Sarah Ahmed', color: 'navy' },
      { name: 'Omar Al-Rashidi', color: 'blue' },
      { name: 'Priya Nair', color: 'navy' },
      { name: 'Lena Fischer', color: 'blue' },
    ],
    documents: [
      { id: 'doc-1', name: 'Project_Proposal.pdf', size: 2_411_520, status: 'uploaded' },
      { id: 'doc-2', name: 'Requirements_Spec.docx', size: 861_184, status: 'uploaded' },
    ],
  },
  {
    id: 'smart-campus-energy',
    name: 'Smart Campus Energy Monitor',
    description:
      'An IoT-based system that tracks real-time energy consumption across campus buildings and uses predictive analytics to recommend efficiency improvements.',
    status: 'Active',
    health: 'Good',
    progress: 65,
    startDate: '2026-06-01',
    dueDate: '2026-11-10',
    team: [
      { name: 'Sarah Ahmed', color: 'navy' },
      { name: 'Khalid Al-Otaibi', color: 'blue' },
      { name: 'Noor Al-Harbi', color: 'navy' },
    ],
    documents: [{ id: 'doc-3', name: 'Sensor_Architecture.pdf', size: 1_205_760, status: 'uploaded' }],
  },
  {
    id: 'ai-study-planner',
    name: 'AI-Powered Study Planner',
    description:
      'A mobile app that generates personalized study schedules using spaced-repetition algorithms and calendar integration.',
    status: 'Planning',
    health: 'Critical',
    progress: 18,
    startDate: '2026-05-20',
    dueDate: '2026-10-05',
    team: [
      { name: 'Sarah Ahmed', color: 'navy' },
      { name: 'Yousef Al-Dosari', color: 'blue' },
    ],
    documents: [],
  },
]

function getProjects() {
  return projects
}

function getProjectById(id) {
  return projects.find((project) => project.id === id)
}

export { getProjects, getProjectById }
