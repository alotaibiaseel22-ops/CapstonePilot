import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  ArrowLeft,
  FolderPlus,
  FileText,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Users,
  Loader2,
} from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { FileUploadZone } from '../components/FileUploadZone'
import { ShareModal } from '../components/ShareModal'
import { ProjectScheduleDialog } from '../components/ProjectScheduleDialog'
import { useCreateProject } from '../hooks/useProjects'
import { generatePlan } from '../api/projects'
import { useJobStatus } from '@/features/planning/hooks/useJobStatus'

function CreateProjectPage() {
  const createProject = useCreateProject()
  const generatePlanMutation = useMutation({
    mutationFn: ({ projectId, file }) => generatePlan(projectId, file),
  })

  const [project, setProject] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const [shareOpen, setShareOpen] = useState(false)
  const [scheduleSaved, setScheduleSaved] = useState(false)

  const { data: job } = useJobStatus(jobId)
  const generating = createProject.isPending || generatePlanMutation.isPending
  const planGenerating = Boolean(jobId) && job?.status !== 'succeeded' && job?.status !== 'failed'
  const quotaExceeded = job?.status === 'failed' && job.error?.startsWith('QUOTA_EXCEEDED')
  // Covers both onboarding triggers: right after plan generation settles,
  // and immediately when no proposal was uploaded at all (jobId never got
  // set, so there's no job to wait on).
  const needsSchedule = Boolean(project) && !planGenerating && !scheduleSaved

  function handleFileSelected(fileList) {
    setFile(fileList[0] ?? null)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (generating) return
    setError(null)
    try {
      const created = await createProject.mutateAsync({ name, description })
      setProject(created)

      if (file) {
        try {
          const { job_id } = await generatePlanMutation.mutateAsync({ projectId: created.id, file })
          setJobId(job_id)
        } catch {
          // Project creation already succeeded - plan generation failing shouldn't
          // block the user from reaching their project, just skip the job state.
        }
      }
    } catch {
      setError('Could not create the project. Please check the form and try again.')
    }
  }

  return (
    <div className="space-y-6">
      <Link
        to="/projects"
        className="flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-gray-700"
      >
        <ArrowLeft className="size-4" />
        Back to Projects
      </Link>

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
        <p className="mt-1 text-muted-foreground">
          {planGenerating
            ? 'Your AI Project Manager is building your plan...'
            : needsSchedule
              ? 'One more step before your project is ready.'
              : project
                ? 'Your project is ready.'
                : 'CapstonePilot will generate a full AI-powered project plan after setup.'}
        </p>
      </div>

      {planGenerating ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <Loader2 className="size-8 animate-spin text-blue-600" />
            <div>
              <p className="font-semibold text-gray-900">
                Your AI Project Manager is building your plan...
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Analyzing your specification and drafting milestones and tasks. This usually
                takes under a minute.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : needsSchedule ? (
        <ProjectScheduleDialog projectId={project.id} onSaved={() => setScheduleSaved(true)} />
      ) : !project ? (
        <Card>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6">
              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                  1. PROJECT NAME
                </label>
                <Input
                  icon={FolderPlus}
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="ML-Based Traffic Optimization"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                  2. PROJECT DESCRIPTION
                </label>
                <Textarea
                  icon={FileText}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What is this project about?"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                  3. UPLOAD PROJECT SPECIFICATION (OPTIONAL)
                </label>
                <p className="mb-3 text-sm text-muted-foreground">
                  CapstonePilot's AI will read this to generate your initial plan, milestones,
                  tasks, risks, and recommendations. The file itself is never stored.
                </p>
                <FileUploadZone
                  onFilesSelected={handleFileSelected}
                  accept=".pdf,.docx"
                  multiple={false}
                  formatsCaption="Supported formats: PDF, DOCX"
                />
                {file && <p className="mt-2 text-sm text-gray-700">Selected: {file.name}</p>}
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button type="submit" size="lg" className="w-full" disabled={generating}>
                <Sparkles className="size-5" />
                {generating ? 'Generating...' : '4. Generate AI Project Plan'}
              </Button>
            </CardContent>
          </form>
        </Card>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardContent className="flex items-start gap-3">
              {job?.status === 'failed' || (file && !jobId) ? (
                <AlertTriangle className="size-6 shrink-0 text-amber-600" />
              ) : (
                <CheckCircle2 className="size-6 shrink-0 text-green-600" />
              )}
              <div>
                <p className="font-semibold text-gray-900">"{project.name}" was created</p>
                {job?.status === 'succeeded' ? (
                  <p className="text-sm text-muted-foreground">
                    Your AI Project Manager generated an initial plan from your specification.
                    Review and approve it from the project's Plan page before it goes live.
                  </p>
                ) : quotaExceeded ? (
                  <p className="text-sm text-amber-700">
                    The Gemini API quota has been exceeded, so a plan couldn't be generated right
                    now. Please try again later — the AI plan starts empty in the meantime.
                  </p>
                ) : job?.status === 'failed' || (file && !jobId) ? (
                  <p className="text-sm text-muted-foreground">
                    We couldn't generate a plan from your specification, so the AI plan starts
                    empty — you can add milestones and tasks from the project's plan view.
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No specification was uploaded, so the AI plan starts empty — you can add
                    milestones and tasks from the project's plan view.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="w-full"
              onClick={() => setShareOpen(true)}
            >
              <Users className="size-5" />
              Invite Team Members
            </Button>
            <Link to={`/projects/${project.id}`}>
              <Button type="button" size="lg" className="w-full">
                Go to Project
                <ArrowRight className="size-5" />
              </Button>
            </Link>
          </div>

          <ShareModal open={shareOpen} onClose={() => setShareOpen(false)} project={project} />
        </div>
      )}
    </div>
  )
}

export { CreateProjectPage }
