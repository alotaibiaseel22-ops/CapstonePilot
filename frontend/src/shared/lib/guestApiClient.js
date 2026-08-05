import axios from 'axios'

// Separate from apiClient.js by design: a guest session and an owner login
// must be able to coexist in the same browser (e.g. an owner testing their
// own shared link) without clobbering each other's token, and a guest's
// session expiring must never trigger apiClient's hard redirect to /login -
// a guest has no login to redirect to.
const guestApiClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
})

function guestSessionKey(invitationToken) {
  return `capstonepilot_guest_${invitationToken}`
}

function getStoredGuestSession(invitationToken) {
  const raw = localStorage.getItem(guestSessionKey(invitationToken))
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function storeGuestSession(invitationToken, session) {
  localStorage.setItem(
    guestSessionKey(invitationToken),
    JSON.stringify({
      guest_access_token: session.guest_access_token,
      project_id: session.project_id,
      guest: session.guest,
    }),
  )
}

function clearGuestSession(invitationToken) {
  localStorage.removeItem(guestSessionKey(invitationToken))
}

// The invitation token a request is for is threaded through per-call via
// config, not a module-level "current session" - a page could plausibly
// hold sessions for more than one invitation token at once (e.g. two tabs).
guestApiClient.interceptors.request.use((config) => {
  const invitationToken = config.guestInvitationToken
  if (invitationToken) {
    const session = getStoredGuestSession(invitationToken)
    if (session?.guest_access_token) {
      config.headers.Authorization = `Bearer ${session.guest_access_token}`
    }
  }
  return config
})

guestApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const invitationToken = error.config?.guestInvitationToken
    if (error.response?.status === 401 && invitationToken) {
      // Unlike apiClient's owner-side interceptor, this never hard-redirects -
      // GuestSessionProvider reads this cleared state and shows an inline
      // "rejoin" prompt instead.
      clearGuestSession(invitationToken)
    }
    return Promise.reject(error)
  },
)

export { guestApiClient, getStoredGuestSession, storeGuestSession, clearGuestSession }
