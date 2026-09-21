import json
import re


class ManifestError(Exception):
    pass

def clean_version(version_str: str) -> str:
    if not version_str or version_str in ["*", "latest"] or version_str.startswith(("git", "file:", "http")):
        return "unknown"
    # Remove operators ^, ~, >=, <=, >, <, =
    cleaned = re.sub(r'[\^~=><]', '', version_str).strip()
    # If range provided like "1.2.0 - 2.0.0", take first portion
    cleaned = cleaned.split()[0]
    return cleaned if cleaned else "unknown"

def parse_package_json(text: str) -> list[dict]:
    try:
        data = json.loads(text)
    except Exception as e:  # noqa: BLE001 -- convert any JSON parse failure into a typed ManifestError
        raise ManifestError(f"Invalid package.json: {e!s}")
    
    deps = {}
    if "dependencies" in data and isinstance(data["dependencies"], dict):
        deps.update(data["dependencies"])
    if "devDependencies" in data and isinstance(data["devDependencies"], dict):
        deps.update(data["devDependencies"])

    result = []
    for name, raw_ver in deps.items():
        result.append({
            "name": name,
            "version": clean_version(str(raw_ver)),
            "ecosystem": "npm"
        })
    return result

def parse_requirements_txt(text: str) -> list[dict]:
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r")) or "://" in line:
            continue
        
        # Remove markers and extras
        line = line.split(";")[0].strip()
        line = re.sub(r'\[.*?\]', '', line)
        
        # Split on operator
        match = re.split(r'==|>=|<=|~=|>|<', line)
        pkg_name = match[0].strip()
        ver = clean_version(match[1].strip()) if len(match) > 1 else "unknown"
        
        if pkg_name:
            result.append({
                "name": pkg_name,
                "version": ver,
                "ecosystem": "pypi"
            })
    return result

def parse_manifests(files: dict[str, str]) -> list[dict]:
    all_deps = []
    for filename, content in files.items():
        if filename == "package.json":
            all_deps.extend(parse_package_json(content))
        elif filename == "requirements.txt":
            all_deps.extend(parse_requirements_txt(content))
    
    # Deduplicate by name and ecosystem
    seen = set()
    unique_deps = []
    for dep in all_deps:
        key = (dep["name"], dep["ecosystem"])
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)
    return unique_deps
