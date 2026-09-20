import re
from github import Github, GithubException
from app.config import settings

class InvalidRepoURL(Exception): pass
class RepoNotFound(Exception): pass
class NoManifestFound(Exception): pass
class GitHubRateLimited(Exception): pass

def parse_repo_url(url: str) -> tuple[str, str]:
    pattern = r"https?://github\.com/([^/]+)/([^/.]+)(?:\.git)?(?:/.*)?"
    match = re.match(pattern, url.strip())
    if not match:
        raise InvalidRepoURL("Invalid GitHub repository URL.")
    return match.group(1), match.group(2)

def fetch_repo_data(url: str):
    owner, name = parse_repo_url(url)
    g = Github(settings.GITHUB_TOKEN) if settings.GITHUB_TOKEN else Github()
    
    try:
        repo = g.get_repo(f"{owner}/{name}")
        files = {}
        
        # Check package.json
        try:
            pjson = repo.get_contents("package.json")
            files["package.json"] = pjson.decoded_content.decode("utf-8")
        except GithubException:
            pass

        # Check requirements.txt
        try:
            reqs = repo.get_contents("requirements.txt")
            files["requirements.txt"] = reqs.decoded_content.decode("utf-8")
        except GithubException:
            pass

        if not files:
            raise NoManifestFound("No package.json or requirements.txt found in repository root.")

        spdx_id = repo.license.spdx_id if repo.license and repo.license.spdx_id != "NOASSERTION" else None
        
        return {
            "owner": owner,
            "name": name,
            "files": files,
            "license": spdx_id
        }
    except GithubException as e:
        if e.status == 404:
            raise RepoNotFound("Repository not found or it is private.")
        elif e.status == 403 and "rate limit" in str(e).lower():
            raise GitHubRateLimited("GitHub rate limit reached. Try again later.")
        raise