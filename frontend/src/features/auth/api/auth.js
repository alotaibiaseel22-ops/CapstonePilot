import { apiClient } from '@/shared/lib/apiClient'

async function login(email, password) {
  const body = new URLSearchParams()
  body.set('username', email)
  body.set('password', password)

  const { data } = await apiClient.post('/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

async function getCurrentUser() {
  const { data } = await apiClient.get('/users/me')
  return data
}

export { login, getCurrentUser }
