import { useState } from 'react'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { FileUploadZone } from './FileUploadZone'
import { useAnalyzeProposal } from '../hooks/useAnalyzeProposal'

function ProposalUploadSection({ projectId }) {
  const analyze = useAnalyzeProposal(projectId)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function handleFilesSelected(fileList) {
    const file = fileList[0]
    if (!file) return
    setError(null)
    setResult(null)
    analyze.mutate(file, {
      onSuccess: (data) => setResult(data),
      onError: (err) => setError(err.response?.data?.detail ?? 'Could not analyze this file.'),
    })
  }

  return (
    <div>
      <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
        UPLOAD PROJECT PROPOSAL (OPTIONAL)
      </label>
      <p className="mb-3 text-sm text-muted-foreground">
        CapstonePilot's AI agents will read this file to generate the initial project plan, detect
        risks, and produce recommendations. The file itself is never stored — only the AI's analysis
        is kept.
      </p>

      <FileUploadZone
        onFilesSelected={handleFilesSelected}
        accept=".pdf,.docx,.txt"
        multiple={false}
        formatsCaption="Supported formats: PDF, DOCX, TXT · Max file size: 20 MB"
      />

      {analyze.isPending && (
        <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Analyzing proposal...
        </p>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {result && (
        <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="flex items-center gap-2 font-semibold text-green-800">
            <CheckCircle2 className="size-4" />
            {result.message}
          </p>
          {result.preview && (
            <p className="mt-2 text-sm text-green-700">&ldquo;{result.preview}&hellip;&rdquo;</p>
          )}
        </div>
      )}
    </div>
  )
}

export { ProposalUploadSection }
