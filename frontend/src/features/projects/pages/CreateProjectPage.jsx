import { useState } from 'react'
import { FolderPlus, FileText, Calendar, Users, Sparkles } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { TeamMemberChip } from '../components/TeamMemberChip'

const initialTeam = [
  { name: 'Omar Al-Rashidi', color: 'blue' },
  { name: 'Priya Nair', color: 'navy' },
]

function CreateProjectPage() {
  const [team, setTeam] = useState(initialTeam)
  const [memberInput, setMemberInput] = useState('')

  function handleAddMember(e) {
    if (e.key !== 'Enter' || !memberInput.trim()) return
    e.preventDefault()
    setTeam((prev) => [...prev, { name: memberInput.trim(), color: 'blue' }])
    setMemberInput('')
  }

  function handleRemoveMember(name) {
    setTeam((prev) => prev.filter((member) => member.name !== name))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
        <p className="mt-1 text-muted-foreground">
          CapstonePilot will generate a full AI-powered project plan after setup.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-6">
          <div>
            <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">PROJECT NAME</label>
            <Input icon={FolderPlus} defaultValue="ML-Based Traffic Optimization" />
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
              PROJECT DESCRIPTION
            </label>
            <Textarea
              icon={FileText}
              defaultValue="A machine learning system that analyzes real-time traffic data to optimize signal timing and reduce congestion in urban intersections. The system will use LSTM neural networks for prediction and a React-based dashboard for monitoring."
            />
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">START DATE</label>
              <Input icon={Calendar} type="date" defaultValue="2026-07-15" />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">DEADLINE</label>
              <Input icon={Calendar} type="date" defaultValue="2026-12-01" />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">TEAM MEMBERS</label>
            <Input
              icon={Users}
              placeholder="Add team member name..."
              value={memberInput}
              onChange={(e) => setMemberInput(e.target.value)}
              onKeyDown={handleAddMember}
            />
            <div className="mt-3 flex flex-wrap gap-2">
              {team.map((member) => (
                <TeamMemberChip
                  key={member.name}
                  name={member.name}
                  color={member.color}
                  onRemove={() => handleRemoveMember(member.name)}
                />
              ))}
            </div>
          </div>

          <Button type="button" size="lg" className="w-full">
            <Sparkles className="size-5" />
            Generate Project Plan with AI
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export { CreateProjectPage }
