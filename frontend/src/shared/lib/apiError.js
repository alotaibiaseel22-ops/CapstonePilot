/**
 * Turns an axios error into a message worth showing a user, and always logs
 * the full error to the console first - the UI message is necessarily a
 * simplification, the console is where the real detail belongs.
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

  console.error('API error response:', error.response.status, error.response.data)

  const detail = error.response.data?.detail

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
