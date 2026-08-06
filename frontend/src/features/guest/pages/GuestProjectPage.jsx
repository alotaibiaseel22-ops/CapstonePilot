import { useState } from 'react'
import { useQueries, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Circle, CircleDot, Send } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Card } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Progress } from '@/shared/components/ui/progress'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { useGuestSession } from '@/app/providers/GuestSessionProvider'
import {
  getGuestProject,
  getGuestMembers,
  getGuestGuests,
  getGuestMilestones,
  getGuestTasks,
  updateGuestTaskStatus,
  getGuestAttachments,
  uploadGuestAttachment,
  downloadGuestAttachment,
  deleteGuestAttachment,
  getGuestComments,
  postGuestComment,
  deleteGuestComment,
} from '../api/guest'
import { getApiErrorMessage } from '@/shared/lib/apiError'
import { cn } from '@/shared/lib/utils'
import { AttachmentRow } from '@/features/attachments/components/AttachmentRow'
import { CommentRow } from '@/features/comments/components/CommentRow'
import { FileUploadZone } from '@/features/projects/components/FileUploadZone'

const statusMeta = {
  pending: { label: 'Pending', tone: 'default', value: 0, icon: Circle },
  in_progress: { label: 'In Progress', tone: 'info', value: 50, icon: CircleDot },
  done: { label: 'Done', tone: 'success', value: 100, icon: CheckCircle2 },
}
const NEXT_STATUS = { pending: 'in_progress', in_progress: 'done', done: 'pending' }

function GuestTaskRow({ task, invitationToken, guestId, onSessionInvalid }) {
  const queryClient = useQueryClient()
  const isMine = task.assignee_guest_id === guestId
  const meta = statusMeta[task.status]
  const StatusIcon = meta.icon
  const done = task.status === 'done'

  const updateStatus = useMutation({
    mutationFn: (nextStatus) => updateGuestTaskStatus(invitationToken, task.id, nextStatus),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['guest', invitationToken, 'tasks'] }),
    onError: (err) => {
      if (err.response?.status === 401) onSessionInvalid()
    },
  })

  return (
    <div className="flex items-center gap-3 border-t border-border px-6 py-4">
      <button
        type="button"
        onClick={() => isMine && updateStatus.mutate(NEXT_STATUS[task.status])}
        disabled={!isMine || updateStatus.isPending}
        aria-label={isMine ? `Advance status for ${task.title}` : `${task.title} (not assigned to you)`}
        className="shrink-0 disabled:opacity-40"
        title={isMine ? undefined : 'Only tasks assigned to you can be updated'}
      >
        <StatusIcon
          className={cn(
            'size-5',
            done ? 'text-green-600' : task.status === 'in_progress' ? 'text-blue-500' : 'text-gray-300',
          )}
        />
      </button>
      <p className={cn('flex-1 text-sm text-gray-800', done && 'text-muted-foreground line-through')}>
        {task.title}
      </p>
      {isMine && <Badge variant="info">Assigned to you</Badge>}
      <Badge variant={meta.tone}>{meta.label}</Badge>
      <Progress value={meta.value} className="w-20" />
    </div>
  )
}

async function triggerGuestDownload(invitationToken, projectId, attachment) {
  const blob = await downloadGuestAttachment(invitationToken, projectId, attachment.id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = attachment.filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function GuestAttachmentsSection({
  invitationToken,
  projectId,
  guestId,
  members,
  guests,
  onSessionInvalid,
}) {
  const queryClient = useQueryClient()
  const queryKey = ['guest', invitationToken, 'attachments']

  const { data: attachments, isLoading } = useQuery({
    queryKey,
    queryFn: () => getGuestAttachments(invitationToken, projectId),
    enabled: Boolean(projectId),
  })

  const upload = useMutation({
    mutationFn: (file) => uploadGuestAttachment(invitationToken, projectId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
    onError: (err) => {
      if (err.response?.status === 401) onSessionInvalid()
    },
  })
  const remove = useMutation({
    mutationFn: (attachmentId) => deleteGuestAttachment(invitationToken, projectId, attachmentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
    onError: (err) => {
      if (err.response?.status === 401) onSessionInvalid()
    },
  })

  return (
    <Card className="overflow-hidden">
      <div className="p-6 pb-0">
        <h2 className="font-bold text-gray-900">Attachments</h2>
      </div>
      <div className="p-6">
        <FileUploadZone
          onFilesSelected={(files) => Array.from(files).forEach((f) => upload.mutate(f))}
          formatsCaption="Max file size: 20 MB"
        />
      </div>
      {isLoading && <LoadingState label="Loading attachments..." />}
      {!isLoading && attachments.length === 0 && (
        <p className="border-t border-border px-6 py-4 text-sm text-muted-foreground">
          No attachments yet.
        </p>
      )}
      {!isLoading &&
        attachments.map((attachment) => (
          <AttachmentRow
            key={attachment.id}
            attachment={attachment}
            members={members}
            guests={guests}
            currentGuestId={guestId}
            onDownload={(a) => triggerGuestDownload(invitationToken, projectId, a)}
            onDelete={(attachmentId) => remove.mutate(attachmentId)}
            deleting={remove.isPending}
          />
        ))}
    </Card>
  )
}

function GuestCommentsSection({
  invitationToken,
  projectId,
  guestId,
  members,
  guests,
  onSessionInvalid,
}) {
  const queryClient = useQueryClient()
  const queryKey = ['guest', invitationToken, 'comments']
  const [body, setBody] = useState('')

  const { data: comments, isLoading } = useQuery({
    queryKey,
    queryFn: () => getGuestComments(invitationToken, projectId),
    enabled: Boolean(projectId),
  })

  const post = useMutation({
    mutationFn: (commentBody) => postGuestComment(invitationToken, projectId, commentBody),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setBody('')
    },
    onError: (err) => {
      if (err.response?.status === 401) onSessionInvalid()
    },
  })
  const remove = useMutation({
    mutationFn: (commentId) => deleteGuestComment(invitationToken, projectId, commentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
    onError: (err) => {
      if (err.response?.status === 401) onSessionInvalid()
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = body.trim()
    if (trimmed) post.mutate(trimmed)
  }

  return (
    <Card className="overflow-hidden">
      <div className="p-6 pb-0">
        <h2 className="font-bold text-gray-900">Comments</h2>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-2 p-6">
        <Textarea
          className="min-h-20"
          placeholder="Write a comment..."
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <Button type="submit" className="self-end" disabled={!body.trim() || post.isPending}>
          <Send className="size-4" />
          Post Comment
        </Button>
      </form>
      {isLoading && <LoadingState label="Loading comments..." />}
      {!isLoading && comments.length === 0 && (
        <p className="border-t border-border px-6 py-4 text-sm text-muted-foreground">
          No comments yet - start the discussion.
        </p>
      )}
      {!isLoading &&
        comments.map((comment) => (
          <CommentRow
            key={comment.id}
            comment={comment}
            members={members}
            guests={guests}
            currentGuestId={guestId}
            onDelete={(commentId) => remove.mutate(commentId)}
            deleting={remove.isPending}
          />
        ))}
    </Card>
  )
}

function GuestProjectPage() {
  const { invitationToken, session, markSessionInvalid } = useGuestSession()
  const projectId = session?.project_id
  const guestId = session?.guest?.id

  const { data: project, isLoading: projectLoading, isError: projectError, error: projectErr } = useQuery({
    queryKey: ['guest', invitationToken, 'project'],
    queryFn: () => getGuestProject(invitationToken, projectId),
    enabled: Boolean(projectId),
  })

  const {
    data: milestones,
    isLoading: milestonesLoading,
    isError: milestonesError,
    error: milestonesErr,
  } = useQuery({
    queryKey: ['guest', invitationToken, 'milestones'],
    queryFn: () => getGuestMilestones(invitationToken, projectId),
    enabled: Boolean(projectId),
  })

  const taskQueries = useQueries({
    queries: (milestones ?? []).map((m) => ({
      queryKey: ['guest', invitationToken, 'tasks', m.id],
      queryFn: () => getGuestTasks(invitationToken, m.id),
      enabled: Boolean(milestones),
    })),
  })

  const { data: members = [] } = useQuery({
    queryKey: ['guest', invitationToken, 'members'],
    queryFn: () => getGuestMembers(invitationToken, projectId),
    enabled: Boolean(projectId),
  })
  const { data: guests = [] } = useQuery({
    queryKey: ['guest', invitationToken, 'guests'],
    queryFn: () => getGuestGuests(invitationToken, projectId),
    enabled: Boolean(projectId),
  })

  const activeError = projectErr ?? milestonesErr
  if (activeError?.response?.status === 401 || activeError?.response?.status === 403) {
    markSessionInvalid()
    return null
  }

  const isLoading = projectLoading || milestonesLoading
  const isError = projectError || milestonesError

  if (isLoading) return <LoadingState label="Loading project..." />
  if (isError) return <ErrorState message={getApiErrorMessage(activeError, "Couldn't load this project.")} />

  const allTasks = taskQueries.flatMap((q) => q.data ?? [])
  const totalTasks = allTasks.length
  const doneTasks = allTasks.filter((t) => t.status === 'done').length
  const overallPercent = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0
  const myTaskCount = allTasks.filter((t) => t.assignee_guest_id === guestId).length
  // list_members never includes the project owner - without this, an
  // owner-authored attachment/comment resolves to no match and shows as
  // "Unknown" (same reasoning as AttachmentsPage.jsx/CommentsPage.jsx).
  const allMembers = [{ user_id: project.owner_id, name: project.owner_name }, ...members]

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          {project.description && <p className="mt-1 text-muted-foreground">{project.description}</p>}
          {myTaskCount > 0 && (
            <p className="mt-2 text-sm text-blue-600">
              {myTaskCount} task{myTaskCount === 1 ? '' : 's'} assigned to you
            </p>
          )}
        </div>
        <span className="rounded-full border border-border bg-white px-4 py-2 text-sm">
          Progress <span className="font-bold text-blue-600">{overallPercent}%</span>
        </span>
      </div>

      {(milestones ?? []).length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center text-muted-foreground">
          No milestones yet for this project.
        </div>
      ) : (
        <div className="space-y-4">
          {milestones.map((milestone, index) => {
            const tasks = taskQueries[index]?.data ?? []
            const done = tasks.filter((t) => t.status === 'done').length
            const value = tasks.length > 0 ? Math.round((done / tasks.length) * 100) : 0
            return (
              <Card key={milestone.id} className="overflow-hidden">
                <div className="p-6">
                  <p className="font-bold text-gray-900">{milestone.title}</p>
                  <div className="mt-2 flex items-center gap-3">
                    <Progress value={value} className="max-w-xs" />
                    <span className="shrink-0 text-sm font-medium text-gray-700">{value}%</span>
                  </div>
                </div>
                {taskQueries[index]?.isLoading && <LoadingState label="Loading tasks..." />}
                {tasks.length === 0 && !taskQueries[index]?.isLoading && (
                  <p className="border-t border-border px-6 py-4 text-sm text-muted-foreground">
                    No tasks yet for this milestone.
                  </p>
                )}
                {tasks.map((task) => (
                  <GuestTaskRow
                    key={task.id}
                    task={task}
                    invitationToken={invitationToken}
                    guestId={guestId}
                    onSessionInvalid={markSessionInvalid}
                  />
                ))}
              </Card>
            )
          })}
        </div>
      )}

      <GuestAttachmentsSection
        invitationToken={invitationToken}
        projectId={projectId}
        guestId={guestId}
        members={allMembers}
        guests={guests}
        onSessionInvalid={markSessionInvalid}
      />
      <GuestCommentsSection
        invitationToken={invitationToken}
        projectId={projectId}
        guestId={guestId}
        members={allMembers}
        guests={guests}
        onSessionInvalid={markSessionInvalid}
      />
    </div>
  )
}

export { GuestProjectPage }
