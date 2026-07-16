import { Modal } from './modal'
import { Button } from './button'

function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isConfirming = false,
  destructive = false,
}) {
  return (
    <Modal open={open} onClose={onClose} title={title} className="max-w-md">
      <p className="text-sm text-muted-foreground">{description}</p>
      <div className="mt-6 flex justify-end gap-3">
        <Button type="button" variant="outline" onClick={onClose} disabled={isConfirming}>
          {cancelLabel}
        </Button>
        <Button
          type="button"
          variant="destructive"
          className={
            destructive
              ? 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'
              : 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100'
          }
          onClick={onConfirm}
          disabled={isConfirming}
        >
          {isConfirming ? 'Please wait...' : confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}

export { ConfirmDialog }
