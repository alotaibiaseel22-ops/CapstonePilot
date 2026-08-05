/**
 * Turns an axios error into a message worth showing a user, and always logs
 * the full error to the console first - the UI message is necessarily a
 * simplification, the console is where the real detail belongs.
 *
 * Status codes with an unambiguous, generic meaning get a fixed message
 * regardless of what the backend put in `detail` (e.g. a 401 always means
 * "wrong credentials" - real for login, and elsewhere in the app a 401
 * instead triggers apiClient.js's own redirect-to-login before any inline
 * message would even be seen, so this message is never actually shown out
 * of context). Everything else (400/422 validation, 409 conflicts, etc.)
 * still surfaces the backend's own `detail`, since those are meaningful
 * per-endpoint and the backend already writes a specific message for them.
 */
function getApiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  console.error('API request failed:', error)

  if (!error?.response) {
    // Axios only omits `response` when nothing came back at all: the backend
    // is unreachable/down, a network failure, or a CORS rejection - not a
    // validation error, which always has a response.
    console.error('No response received - the backend may be unreachable or CORS may be blocking the request.')
    return 'Could not reach the server. Check your connection and that the backend is running, then try again.'
  }

  const { status, data } = error.response
  console.error('API error response:', status, data)

  if (status === 401) {
    return 'Invalid email or password.'
  }
  if (status === 403) {
    return 'You are not authorized to perform this action.'
  }
  if (status === 404) {
    return 'Requested resource not found.'
  }
  if (status >= 500) {
    return 'Server error. Please try again later.'
  }

  // 400/422 (validation) and anything else not covered above - show the
  // backend's own detail message when it has one.
  const detail = data?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    // FastAPI/Pydantic validation error shape: [{ loc, msg, type }, ...]
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : null
        return field && typeof field === 'string' ? `${field}: ${item.msg}` : item.msg
      })
      .filter(Boolean)
      .join(' ')
  }

  return fallback
}

export { getApiErrorMessage }
