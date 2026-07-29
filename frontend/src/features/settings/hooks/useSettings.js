import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuth } from '@/app/providers/AuthProvider'
import { updateProfile, changePassword } from '../api/settings'

function useUpdateProfile() {
  const { refreshUser } = useAuth()
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await refreshUser()
      toast.success('Profile updated')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not update your profile.')
    },
  })
}

function useChangePassword() {
  return useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      toast.success('Password changed')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail ?? 'Could not change your password.')
    },
  })
}

export { useUpdateProfile, useChangePassword }
