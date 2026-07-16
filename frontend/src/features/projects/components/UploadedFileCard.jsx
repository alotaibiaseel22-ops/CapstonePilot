import { FileText, X, Loader2 } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { formatBytes } from '@/shared/lib/utils'

const extensionTone = {
  pdf: 'bg-red-100 text-red-600',
  docx: 'bg-blue-100 text-blue-600',
  pptx: 'bg-amber-100 text-amber-600',
  txt: 'bg-gray-100 text-gray-600',
}

function UploadedFileCard({ name, size, status, onRemove }) {
  const extension = name.split('.').pop().toLowerCase()

  return (
    <div className="flex items-center gap-3 rounded-lg border border-border bg-white p-3">
      <span className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${extensionTone[extension] ?? extensionTone.txt}`}>
        <FileText className="size-4" />
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-900">{name}</p>
        <p className="text-xs text-muted-foreground">{formatBytes(size)}</p>
      </div>

      {status === 'uploading' ? (
        <Badge variant="info" className="flex shrink-0 items-center gap-1">
          <Loader2 className="size-3 animate-spin" />
          Uploading
        </Badge>
      ) : (
        <Badge variant="success" className="shrink-0">
          Uploaded
        </Badge>
      )}

      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${name}`}
        className="shrink-0 text-gray-400 hover:text-gray-600"
      >
        <X className="size-4" />
      </button>
    </div>
  )
}

export { UploadedFileCard }
