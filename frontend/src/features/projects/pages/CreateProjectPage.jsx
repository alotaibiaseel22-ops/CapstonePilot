import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FolderPlus, FileText, Sparkles, CheckCircle2, ArrowRight, Users } from 'lucide-react'
import { Card, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { FileUploadZone } from '../components/FileUploadZone'
import { useCreateProject } from '../hooks/useProjects'
import { useAnalyzeProposal } from '../hooks/useAnalyzeProposal'

function CreateProjectPage() {
  const createProject = useCreateProject()
  const analyzeProposal = useAnalyzeProposal()

  const [project, setProject] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)

  const generating = createProject.isPending || analyzeProposal.isPending

  function handleFileSelected(fileList) {
    setFile(fileList[0] ?? null)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      const created = await createProject.mutateAsync({ name, description })
      setProject(created)

      if (file) {
        const result = await analyzeProposal.mutateAsync({ projectId: created.id, file })
        setAnalysis(result)
      }
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
            ? 'Your AI-powered project plan is ready.'
            : 'CapstonePilot will generate a full AI-powered project plan after setup.'}
        </p>
      </div>

      {!project ? (
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
              <CheckCircle2 className="size-6 shrink-0 text-green-600" />
              <div>
                <p className="font-semibold text-gray-900">"{project.name}" was created</p>
                {analysis ? (
                  <>
                    <p className="text-sm text-muted-foreground">{analysis.message}</p>
                    {analysis.preview && (
                      <p className="mt-2 text-sm italic text-gray-500">
                        &ldquo;{analysis.preview}&hellip;&rdquo;
                      </p>
                    )}
                  </>
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
            <Link to={`/projects/${project.id}/settings`}>
              <Button type="button" variant="outline" size="lg" className="w-full">
                <Users className="size-5" />
                Invite Team Members
              </Button>
            </Link>
            <Link to={`/projects/${project.id}`}>
              <Button type="button" size="lg" className="w-full">
                Go to Project
                <ArrowRight className="size-5" />
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export { CreateProjectPage }
