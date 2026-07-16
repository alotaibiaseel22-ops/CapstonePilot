import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FolderPlus, FileText, Calendar, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { useCreateProject } from '../hooks/useProjects'
import { TeamMembersSection } from '../components/TeamMembersSection'
import { ProposalUploadSection } from '../components/ProposalUploadSection'

function CreateProjectPage() {
  const createProject = useCreateProject()
  const [project, setProject] = useState(null)
  const [form, setForm] = useState({ name: '', description: '', start_date: '', due_date: '' })
  const [error, setError] = useState(null)

  function updateField(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      const created = await createProject.mutateAsync({
        name: form.name,
        description: form.description,
        start_date: form.start_date || null,
        due_date: form.due_date || null,
      })
      setProject(created)
    } catch {
      setError('Could not create the project. Please check the form and try again.')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
        <p className="mt-1 text-muted-foreground">
          {project
            ? 'Add your team and, optionally, a project proposal for AI analysis.'
            : "CapstonePilot will generate a full AI-powered project plan after setup."}
        </p>
      </div>

      {!project ? (
        <Card>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6">
              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                  PROJECT NAME
                </label>
                <Input
                  icon={FolderPlus}
                  required
                  value={form.name}
                  onChange={updateField('name')}
                  placeholder="ML-Based Traffic Optimization"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                  PROJECT DESCRIPTION
                </label>
                <Textarea
                  icon={FileText}
                  value={form.description}
                  onChange={updateField('description')}
                  placeholder="What is this project about?"
                />
              </div>

              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                    START DATE
                  </label>
                  <Input icon={Calendar} type="date" value={form.start_date} onChange={updateField('start_date')} />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">DEADLINE</label>
                  <Input icon={Calendar} type="date" value={form.due_date} onChange={updateField('due_date')} />
                </div>
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button type="submit" size="lg" className="w-full" disabled={createProject.isPending}>
                <Sparkles className="size-5" />
                {createProject.isPending ? 'Creating...' : 'Create Project'}
              </Button>
            </CardContent>
          </form>
        </Card>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardContent className="flex items-center gap-3">
              <CheckCircle2 className="size-6 shrink-0 text-green-600" />
              <div>
                <p className="font-semibold text-gray-900">"{project.name}" was created</p>
                <p className="text-sm text-muted-foreground">
                  Add your team and an optional proposal below, or continue to the project now.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-6">
              <TeamMembersSection projectId={project.id} />
              <ProposalUploadSection projectId={project.id} />
            </CardContent>
          </Card>

          <Link to={`/projects/${project.id}`}>
            <Button type="button" size="lg" className="w-full">
              Go to Project
              <ArrowRight className="size-5" />
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}

export { CreateProjectPage }
