import { useEffect, useRef, useState } from 'react'
import { FileUploadZone } from './FileUploadZone'
import { UploadedFileCard } from './UploadedFileCard'

const ACCEPTED_EXTENSIONS = ['pdf', 'docx', 'pptx', 'txt']
const MAX_SIZE_BYTES = 20 * 1024 * 1024

function ProjectMaterialsSection() {
  const [files, setFiles] = useState([])
  const [error, setError] = useState(null)
  const timeoutsRef = useRef(new Map())

  useEffect(() => {
    const timeouts = timeoutsRef.current
    return () => {
      timeouts.forEach((timeoutId) => clearTimeout(timeoutId))
    }
  }, [])

  function handleFilesSelected(fileList) {
    const incoming = Array.from(fileList)
    const accepted = []
    const rejected = []

    for (const file of incoming) {
      const extension = file.name.split('.').pop().toLowerCase()
      if (!ACCEPTED_EXTENSIONS.includes(extension)) {
        rejected.push(`${file.name} (unsupported format)`)
      } else if (file.size > MAX_SIZE_BYTES) {
        rejected.push(`${file.name} (exceeds 20 MB)`)
      } else {
        accepted.push(file)
      }
    }

    setError(rejected.length > 0 ? `Couldn't add: ${rejected.join(', ')}` : null)

    const newEntries = accepted.map((file) => ({
      id: `${file.name}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
      name: file.name,
      size: file.size,
      status: 'uploading',
    }))

    if (newEntries.length === 0) return

    setFiles((prev) => [...prev, ...newEntries])

    newEntries.forEach((entry) => {
      const timeoutId = setTimeout(() => {
        setFiles((prev) => prev.map((f) => (f.id === entry.id ? { ...f, status: 'uploaded' } : f)))
        timeoutsRef.current.delete(entry.id)
      }, 700 + Math.random() * 500)
      timeoutsRef.current.set(entry.id, timeoutId)
    })
  }

  function handleRemove(id) {
    const timeoutId = timeoutsRef.current.get(id)
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutsRef.current.delete(id)
    }
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

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
