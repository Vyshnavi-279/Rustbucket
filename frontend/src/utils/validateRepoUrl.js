const URL_RE = /^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+?)(?:\.git)?(?:\/(?:tree\/.*)?)?$/i

// Returns an error message, or null when the URL is valid.
export function validateRepoUrl(url) {
  const value = String(url || '').trim()
  if (!value) return 'Please enter a repository URL.'
  if (!URL_RE.test(value)) {
    return 'Enter a GitHub repository URL like https://github.com/owner/repo'
  }
  return null
}