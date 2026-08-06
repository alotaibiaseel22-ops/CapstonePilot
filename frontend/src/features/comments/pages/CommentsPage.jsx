import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Send } from 'lucide-react'
import { LoadingState } from '@/shared/components/common/LoadingState'
import { ErrorState } from '@/shared/components/common/ErrorState'
import { Card } from '@/shared/components/ui/card'
import { Textarea } from '@/shared/components/ui/textarea'
import { Button } from '@/shared/components/ui/button'
import { useAuth } from '@/app/providers/AuthProvider'
import { useProject } from '@/features/projects/hooks/useProjects'
import { useProjectMembers } from '@/features/projects/hooks/useProjectMembers'
import { useProjectGuests } from '@/features/projects/hooks/useProjectGuests'
import { CommentRow } from '../components/CommentRow'
import { useComments, useDeleteComment, usePostComment } from '../hooks/useComments'

function CommentsPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const [body, setBody] = useState('')
  const { data: project, isLoading: projectLoading, isError: projectError } = useProject(id)
  const { data: members = [] } = useProjectMembers(id)
  const { data: guests = [] } = useProjectGuests(id)
  const { data: comments, isLoading: commentsLoading, isError: commentsError } = useComments(id)
  const postComment = usePostComment(id)
  const deleteComment = useDeleteComment(id)

  const isLoading = projectLoading || commentsLoading
  const isError = projectError || commentsError

  if (isLoading) return <LoadingState label="Loading comments..." />
  if (isError) return <ErrorState message="Couldn't load comments. Please try again." />

  const isOwner = user?.id === project.owner_id
  // list_members never includes the project owner - without this, a
  // comment the owner posted resolves to no match and shows as "Unknown"
  // (same reasoning as AttachmentsPage.jsx / ProgressPage.jsx's picker).
  const allMembers = [{ user_id: project.owner_id, name: project.owner_name }, ...members]

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = body.trim()
    if (!trimmed) return
    postComment.mutate(trimmed, { onSuccess: () => setBody('') })
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
        <h1 className="text-3xl font-bold text-gray-900">Comments</h1>
        <p className="mt-1 text-muted-foreground">{project.name}</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <Textarea
          className="min-h-20"
          placeholder="Write a comment..."
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <Button type="submit" className="self-end" disabled={!body.trim() || postComment.isPending}>
          <Send className="size-4" />
          Post Comment
        </Button>
      </form>

      <Card className="overflow-hidden">
        {comments.length === 0 ? (
          <p className="px-6 py-10 text-center text-sm text-muted-foreground">
            No comments yet - start the discussion.
          </p>
        ) : (
          comments.map((comment) => (
            <CommentRow
              key={comment.id}
              comment={comment}
              members={allMembers}
              guests={guests}
              currentUserId={user?.id}
              isProjectOwner={isOwner}
              onDelete={(commentId) => deleteComment.mutate(commentId)}
              deleting={deleteComment.isPending}
            />
          ))
        )}
      </Card>
    </div>
  )
}

export { CommentsPage }
