import { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

function FileUploadZone({ onFilesSelected, accept, className }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  function openBrowser() {
    inputRef.current?.click()
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files?.length) {
      onFilesSelected(e.dataTransfer.files)
    }
  }

  function handleInputChange(e) {
    if (e.target.files?.length) {
      onFilesSelected(e.target.files)
    }
    e.target.value = ''
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={openBrowser}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && openBrowser()}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={cn(
        'flex cursor-pointer flex-col items-center gap-1 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
        isDragging ? 'border-blue-400 bg-blue-50' : 'border-border bg-gray-50 hover:bg-gray-100',
        className,
      )}
    >
      <UploadCloud className={cn('mb-2 size-8', isDragging ? 'text-blue-600' : 'text-muted-foreground')} />
      <p className="text-sm font-medium text-gray-700">Drag &amp; Drop your project files here</p>
      <p className="text-sm text-blue-600">or click to browse</p>
      <p className="mt-3 text-xs text-muted-foreground">Supported formats: PDF, DOCX, PPTX, TXT &middot; Max file size: 20 MB</p>

      <input ref={inputRef} type="file" multiple accept={accept} onChange={handleInputChange} className="hidden" />
    </div>
  )
}

export { FileUploadZone }
