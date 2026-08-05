import { createContext, useContext, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { guestJoin, getGuestSession } from '@/features/guest/api/guest'
import { getStoredGuestSession, storeGuestSession, clearGuestSession } from '@/shared/lib/guestApiClient'

const GuestSessionContext = createContext(null)

// A guest-only analogue of AuthProvider, deliberately not merged into
// useAuth()'s single owner-shaped status machine - scoped to the
// /guest/:invitationToken route subtree only (see router.jsx).
function GuestSessionProvider({ children }) {
  const { invitationToken } = useParams()
  const [session, setSession] = useState(null)
  // 'loading' | 'needs-join' | 'active'
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    setStatus('loading')
    const stored = getStoredGuestSession(invitationToken)
    if (!stored?.guest_access_token) {
      setStatus('needs-join')
      return
    }
    getGuestSession(invitationToken, stored.guest_access_token)
      .then((data) => {
        storeGuestSession(invitationToken, data)
        setSession(data)
        setStatus('active')
      })
      .catch(() => {
        clearGuestSession(invitationToken)
        setStatus('needs-join')
      })
  }, [invitationToken])

  async function join(displayName) {
    const data = await guestJoin(invitationToken, displayName)
    storeGuestSession(invitationToken, data)
    setSession(data)
    setStatus('active')
    return data
  }

  // Called by guest pages when a request 401s mid-session (e.g. the owner
  // revoked the invitation while this tab was open) - guestApiClient's own
  // interceptor already clears the stored token; this just makes the UI
  // reflect it instead of continuing to render stale project data.
  function markSessionInvalid() {
    clearGuestSession(invitationToken)
    setSession(null)
    setStatus('needs-join')
  }

  return (
    <GuestSessionContext.Provider
      value={{ invitationToken, session, status, join, markSessionInvalid }}
    >
      {children}
    </GuestSessionContext.Provider>
  )
}

function useGuestSession() {
  const context = useContext(GuestSessionContext)
  if (!context) {
    throw new Error('useGuestSession must be used within a GuestSessionProvider')
  }
  return context
}

export { GuestSessionProvider, useGuestSession }
