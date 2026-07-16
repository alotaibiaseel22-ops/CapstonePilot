import { createContext, useContext, useEffect, useState } from 'react'
import { login as loginRequest, register as registerRequest, getCurrentUser } from '@/features/auth/api/auth'

const TOKEN_KEY = 'capstonepilot_token'

const AuthContext = createContext(null)

function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setStatus('unauthenticated')
      return
    }
    getCurrentUser()
      .then((currentUser) => {
        setUser(currentUser)
        setStatus('authenticated')
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        setStatus('unauthenticated')
      })
  }, [])

  async function login(email, password) {
    const data = await loginRequest(email, password)
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setUser(data.user)
    setStatus('authenticated')
  }

  async function register(fields) {
    const data = await registerRequest(fields)
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setUser(data.user)
    setStatus('authenticated')
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
    setStatus('unauthenticated')
  }

  return (
    <AuthContext.Provider value={{ user, status, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export { AuthProvider, useAuth }
