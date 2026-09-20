async function request(path, options) {
  let res
  try {
    res = await fetch(path, options)
  } catch {
    throw new Error('Cannot reach the server. Please try again in a moment.')
  }

  let data
  try {
    data = await res.json()
  } catch {
    data = null
  }

  if (!res.ok) {
    const detail = data && typeof data.detail === 'string' ? data.detail : null
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return data
}

export function submitScan(repoUrl) {
  return request('/api/scans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
  })
}

export function getScan(id) {
  return request(`/api/scans/${id}`)
}

export function listRepos() {
  return request('/api/repos')
}

export function getHistory(repoId) {
  return request(`/api/repos/${repoId}/history`)
}