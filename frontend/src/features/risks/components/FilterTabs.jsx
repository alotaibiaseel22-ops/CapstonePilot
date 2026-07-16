import { cn } from '@/shared/lib/utils'

function FilterTabs({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={cn(
            'rounded-full px-4 py-2 text-sm font-semibold transition-colors',
            option.value === value
              ? 'bg-blue-600 text-white'
              : 'border border-border bg-white text-gray-700 hover:bg-muted',
          )}
        >
          {option.label} ({option.count})
        </button>
      ))}
    </div>
  )
}

export { FilterTabs }
