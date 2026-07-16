import { FileUploadZone } from './FileUploadZone'
import { UploadedFileCard } from './UploadedFileCard'
import { useFileUploads } from '../hooks/useFileUploads'

function ProjectMaterialsSection() {
  const { files, error, handleFilesSelected, handleRemove } = useFileUploads()

  return (
    <div>
      <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">PROJECT MATERIALS</label>
      <p className="mb-3 text-sm text-muted-foreground">
        Upload your proposal, requirements, or planning documents. CapstonePilot's AI agents will analyze them to
        generate the initial project plan, detect risks, and produce recommendations.
      </p>

      <FileUploadZone onFilesSelected={handleFilesSelected} accept=".pdf,.docx,.pptx,.txt" />

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
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
    </div>
  )
}

export { ProjectMaterialsSection }
