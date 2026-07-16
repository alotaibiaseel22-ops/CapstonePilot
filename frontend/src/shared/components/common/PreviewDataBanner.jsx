import { Info } from 'lucide-react'

function PreviewDataBanner({ children }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <Info className="mt-0.5 size-4 shrink-0" />
      <p>{children}</p>
    </div>
  )
}

export { PreviewDataBanner }
