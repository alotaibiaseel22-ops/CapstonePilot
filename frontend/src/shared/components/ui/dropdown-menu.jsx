import { useState } from 'react'
import { cn } from '@/shared/lib/utils'

function DropdownMenu({ trigger, children, align = 'right', menuClassName }) {
  const [open, setOpen] = useState(false)

  function toggle(e) {
    e.stopPropagation()
    e.preventDefault()
    setOpen((o) => !o)
  }

  function close() {
    setOpen(false)
  }

  return (
    <div className="relative inline-block" onClick={(e) => e.stopPropagation()}>
      {trigger({ onClick: toggle, 'aria-expanded': open, 'aria-haspopup': true })}

      {open && (
        <>
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-40 cursor-default"
            onClick={(e) => {
              e.stopPropagation()
              close()
            }}
          />
          <div
            role="menu"
            onClick={close}
            className={cn(
              'absolute z-50 mt-2 min-w-44 rounded-lg border border-border bg-white py-1 shadow-lg',
              align === 'right' ? 'right-0' : 'left-0',
              menuClassName,
            )}
          >
            {children}
          </div>
        </>
      )}
    </div>
  )
}

function DropdownMenuItem({ icon: Icon, destructive, className, children, ...props }) {
  return (
    <button
      type="button"
      role="menuitem"
      className={cn(
        'flex w-full items-center gap-2 px-4 py-2 text-left text-sm',
        destructive ? 'text-red-600 hover:bg-red-50' : 'text-gray-700 hover:bg-muted',
        'disabled:pointer-events-none disabled:opacity-50',
        className,
      )}
      {...props}
    >
      {Icon && <Icon className="size-4" />}
      {children}
    </button>
  )
}

export { DropdownMenu, DropdownMenuItem }
