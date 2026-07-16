import { TriangleAlert } from 'lucide-react'

function ErrorState({ message = 'Something went wrong. Please try again.' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-red-100 bg-red-50 py-16 text-center">
      <TriangleAlert className="size-6 text-red-500" />
      <p className="text-sm text-red-700">{message}</p>
    </div>
  )
}

export { ErrorState }
