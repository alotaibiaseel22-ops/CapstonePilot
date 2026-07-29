import { Sparkles } from 'lucide-react'

function AnalysisBanner() {
  return (
    <div className="flex items-center gap-4 rounded-xl bg-purple-50 p-6">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-white text-purple-600">
        <Sparkles className="size-5" />
      </span>
      <div>
        <p className="font-bold text-gray-900">AI-generated recommendations</p>
        <p className="mt-1 text-sm text-muted-foreground">
          CapstonePilot monitors this project automatically and generates these recommendations
          whenever a risk is detected.
        </p>
      </div>
    </div>
  )
}

export { AnalysisBanner }
