import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Card } from '@/shared/components/ui/card'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProject } from '@/features/projects/hooks/useProjects'
import { useProjectMembers } from '@/features/projects/hooks/useProjectMembers'
import { useProjectGuests } from '@/features/projects/hooks/useProjectGuests'
import { FileUploadZone } from '@/features/projects/components/FileUploadZone'
import { AttachmentRow } from '../components/AttachmentRow'
import { useAttachments, useDeleteAttachment, useUploadAttachment } from '../hooks/useAttachments'
import { downloadAttachment } from '../api/attachments'

async function triggerDownload(projectId, attachment) {
  const blob = await downloadAttachment(projectId, attachment.id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = attachment.filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function AttachmentsPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const { data: project, isLoading: projectLoading, isError: projectError } = useProject(id)
  const { data: members = [] } = useProjectMembers(id)
  const { data: guests = [] } = useProjectGuests(id)
  const { data: attachments, isLoading: attachmentsLoading, isError: attachmentsError } =
    useAttachments(id)
  const upload = useUploadAttachment(id)
  const deleteAttachment = useDeleteAttachment(id)

  const isLoading = projectLoading || attachmentsLoading
  const isError = projectError || attachmentsError

  if (isLoading) return <LoadingState label="Loading attachments..." />
  if (isError) return <ErrorState message="Couldn't load attachments. Please try again." />

  const isOwner = user?.id === project.owner_id
  // list_members never includes the project owner (see ShareModal.jsx /
  // ProgressPage.jsx's assignee picker for the same reasoning) - without
  // this, an attachment the owner uploaded resolves to no match and shows
  // as "Unknown".
  const allMembers = [{ user_id: project.owner_id, name: project.owner_name }, ...members]

  function handleFilesSelected(files) {
    Array.from(files).forEach((file) => upload.mutate(file))
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
        <h1 className="text-3xl font-bold text-gray-900">Attachments</h1>
        <p className="mt-1 text-muted-foreground">{project.name}</p>
      </div>

      <FileUploadZone onFilesSelected={handleFilesSelected} formatsCaption="Max file size: 20 MB" />

      <Card className="overflow-hidden">
        {attachments.length === 0 ? (
          <p className="px-6 py-10 text-center text-sm text-muted-foreground">
            No attachments yet for this project.
          </p>
        ) : (
          attachments.map((attachment) => (
            <AttachmentRow
              key={attachment.id}
              attachment={attachment}
              members={allMembers}
              guests={guests}
              currentUserId={user?.id}
              isProjectOwner={isOwner}
              onDownload={(a) => triggerDownload(id, a)}
              onDelete={(attachmentId) => deleteAttachment.mutate(attachmentId)}
              deleting={deleteAttachment.isPending}
            />
          ))
        )}
      </Card>
    </div>
  )
}

export { AttachmentsPage }
