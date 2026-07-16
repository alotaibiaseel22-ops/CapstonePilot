import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { FileUploadZone } from './FileUploadZone'
import { UploadedFileCard } from './UploadedFileCard'
import { useFileUploads } from '../hooks/useFileUploads'

function DocumentsCard({ initialDocuments = [] }) {
  const { files, error, handleFilesSelected, handleRemove } = useFileUploads(initialDocuments)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Files uploaded here are analyzed by CapstonePilot's AI agents to keep the project plan, risks, and
          recommendations up to date.
        </p>

        <FileUploadZone onFilesSelected={handleFilesSelected} accept=".pdf,.docx,.pptx,.txt" />

        {error && <p className="text-sm text-red-600">{error}</p>}

        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((file) => (
              <UploadedFileCard
                key={file.id}
                name={file.name}
                size={file.size}
                status={file.status}
                onRemove={() => handleRemove(file.id)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export { DocumentsCard }
