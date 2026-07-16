import { useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { ArrowLeft, Trash2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProject, useUpdateProject, useDeleteProject } from '../hooks/useProjects'
import { InviteByEmailForm } from '@/features/invitations/components/InviteByEmailForm'
import { InviteLinkCard } from '@/features/invitations/components/InviteLinkCard'
import { PendingInvitationsList } from '@/features/invitations/components/PendingInvitationsList'

function ProjectSettingsPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const { data: project, isLoading, isError } = useProject(id)
  const updateProject = useUpdateProject(id)
  const deleteProject = useDeleteProject()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [savedMessage, setSavedMessage] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  if (isLoading) return <LoadingState label="Loading project settings..." />
  if (isError || !project) return <ErrorState message="Couldn't load this project." />

  if (project.owner_id !== user?.id) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Project Settings</h1>
        <ErrorState message="Only this project's owner can access its settings." />
      </div>
    )
  }

  const nameValue = name || project.name
  const descriptionValue = description || project.description

  async function handleSave(e) {
    e.preventDefault()
    setSavedMessage(false)
    await updateProject.mutateAsync({ name: nameValue, description: descriptionValue })
    setSavedMessage(true)
  }

  async function handleDelete() {
    await deleteProject.mutateAsync(id)
    navigate('/projects', { replace: true })
  }

  return (
    <div className="space-y-6">
      <Link
        to={`/projects/${id}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-gray-700"
      >
        <ArrowLeft className="size-4" />
        Back to project
      </Link>

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Project Settings</h1>
        <p className="mt-1 text-muted-foreground">{project.name}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                PROJECT NAME
              </label>
              <Input value={nameValue} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                PROJECT DESCRIPTION
              </label>
              <Textarea value={descriptionValue} onChange={(e) => setDescription(e.target.value)} />
            </div>
            {savedMessage && <p className="text-sm text-green-600">Saved.</p>}
            <Button type="submit" size="sm" disabled={updateProject.isPending}>
              {updateProject.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invite Collaborators</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <InviteByEmailForm projectId={id} />
          <InviteLinkCard projectId={id} />
          <div>
            <p className="mb-2 text-xs font-semibold tracking-wide text-gray-500">SENT INVITATIONS</p>
            <PendingInvitationsList projectId={id} />
          </div>
        </CardContent>
      </Card>

      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-700">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent>
          {!confirmingDelete ? (
            <Button type="button" variant="destructive" onClick={() => setConfirmingDelete(true)}>
              <Trash2 className="size-4" />
              Delete Project
            </Button>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-red-700">
                This will permanently delete "{project.name}" and cannot be undone. Are you sure?
              </p>
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="destructive"
                  className="border-red-300 bg-red-50 text-red-700 hover:bg-red-100"
                  onClick={handleDelete}
                  disabled={deleteProject.isPending}
                >
                  {deleteProject.isPending ? 'Deleting...' : 'Yes, delete this project'}
                </Button>
                <Button type="button" variant="outline" onClick={() => setConfirmingDelete(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export { ProjectSettingsPage }
