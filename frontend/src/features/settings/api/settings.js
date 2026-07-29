import { apiClient } from '@/shared/lib/apiClient'

async function updateProfile(payload) {
  const { data } = await apiClient.patch('/users/me', payload)
  return data
}

async function changePassword(payload) {
  await apiClient.post('/users/me/change-password', payload)
}

export { updateProfile, changePassword }
