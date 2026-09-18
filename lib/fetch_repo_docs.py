"""Fetch public Markdown documentation from repositories listed in repos.yaml."""

from __future__ import annotations

import re
import shutil
from pathlib import Path, PurePosixPath

import requests
import yaml


CONFIG_FILE = Path("repos.yaml")
OUTPUT_DIR = Path("source/repos")
GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"
GITHUB_WEB = "https://github.com"
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "paidiver-docs-builder"})

MARKDOWN_LINK = re.compile(r"(!?\[[^]]*\])\(([^)]+)\)")
ASSET_SUFFIXES = {".gif", ".jpeg", ".jpg", ".pdf", ".png", ".svg", ".webp"}


def load_repositories() -> list[dict[str, str]]:
    """Load and validate the repository list."""
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    repositories = config.get("repositories", [])
    if not repositories:
        raise ValueError("repos.yaml does not define any repositories")

    for repository in repositories:
        missing = {"path", "name", "title", "branch"} - repository.keys()
        if missing:
            raise ValueError(f"Repository entry is missing: {', '.join(sorted(missing))}")
        if repository.get("source", "github") != "github":
            raise ValueError(f"Only public GitHub repositories are supported: {repository['path']}")
    return repositories


def repository_tree(repository: dict[str, str]) -> list[dict]:
    """Return the recursive Git tree for a public repository."""
    url = f"{GITHUB_API}/repos/{repository['path']}/git/trees/{repository['branch']}"
    response = SESSION.get(url, params={"recursive": "1"}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("truncated"):
        raise RuntimeError(f"GitHub returned a truncated tree for {repository['path']}")
    return payload.get("tree", [])


def selected_markdown(path: str) -> bool:
    """Select a root README and Markdown below docs/ or deployment/."""
    source = PurePosixPath(path)
    if len(source.parts) == 1:
        return source.name.lower() in {"readme.md", "readme.rst"}
    return source.suffix.lower() == ".md" and source.parts[0].lower() in {"docs", "deployment"}


def raw_url(repository: dict[str, str], path: str) -> str:
    return f"{GITHUB_RAW}/{repository['path']}/{repository['branch']}/{path}"


def web_url(repository: dict[str, str], path: str) -> str:
    return f"{GITHUB_WEB}/{repository['path']}/blob/{repository['branch']}/{path}"


def resolve_source_path(document_path: str, target: str) -> str:
    """Resolve a relative Markdown target without allowing paths above the repo root."""
    combined = PurePosixPath(document_path).parent / target
    parts: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return PurePosixPath(*parts).as_posix()


def rewrite_links(
    content: str,
    document_path: str,
    selected_paths: set[str],
    repository: dict[str, str],
) -> str:
    """Keep copied Markdown links local and send other relative links to GitHub."""

    def replace(match: re.Match[str]) -> str:
        label, original = match.groups()
        target = original.strip()
        if target.startswith(("#", "http://", "https://", "mailto:")):
            return match.group(0)

        path_and_query, fragment = (target.split("#", 1) + [""])[:2]
        path, query = (path_and_query.split("?", 1) + [""])[:2]
        if not path:
            return match.group(0)

        resolved = resolve_source_path(document_path, path)
        suffix = (f"?{query}" if query else "") + (f"#{fragment}" if fragment else "")
        if resolved in selected_paths:
            return f"{label}({path}{suffix})"

        destination = raw_url(repository, resolved) if PurePosixPath(resolved).suffix.lower() in ASSET_SUFFIXES else web_url(repository, resolved)
        return f"{label}({destination}{suffix})"

    return MARKDOWN_LINK.sub(replace, content)


def fetch_markdown(repository: dict[str, str], path: str) -> str:
    response = SESSION.get(raw_url(repository, path), timeout=30)
    response.raise_for_status()
    # A trailing thematic break is harmless in GitHub Markdown but is an invalid
    # document-ending transition in docutils.
    return re.sub(r"\n(?:---|\*\*\*)\s*$", "\n", response.text)


def page_title(path: str) -> str:
    source = PurePosixPath(path)
    if source.name.lower() == "readme.md":
        return source.parent.name.replace("-", " ").title() if source.parent.name else "README"
    return source.stem.replace("-", " ").replace("_", " ").title()


def write_repository_index(repository: dict[str, str], paths: list[str], destination: Path) -> None:
    """Create navigation for one imported repository."""
    readme = next((path for path in paths if path.lower() in {"readme.md", "readme.rst"}), None)
    other_paths = [path for path in paths if path != readme]
    lines = [repository["title"], "=" * len(repository["title"]), ""]
    lines.extend([
        f"Documentation imported from `{repository['path']} <https://github.com/{repository['path']}>`_",
        f"on the ``{repository['branch']}`` branch.",
        "",
        ".. toctree::",
        "   :maxdepth: 2",
        "",
    ])
    if readme:
        lines.append(f"   {PurePosixPath(readme).with_suffix('').as_posix()}")
    lines.extend(f"   {PurePosixPath(path).with_suffix('').as_posix()}" for path in other_paths)
    lines.append("")
    (destination / "index.rst").write_text("\n".join(lines), encoding="utf-8")


def process_repository(repository: dict[str, str]) -> None:
    print(f"Fetching {repository['path']} ({repository['branch']})")
    paths = sorted(
        item["path"]
        for item in repository_tree(repository)
        if item.get("type") == "blob" and selected_markdown(item.get("path", ""))
    )
    if not paths:
        raise RuntimeError(f"No Markdown documentation found in {repository['path']}")

    destination = OUTPUT_DIR / repository["name"]
    destination.mkdir(parents=True, exist_ok=True)
    selected_paths = set(paths)
    for path in paths:
        content = fetch_markdown(repository, path)
        content = rewrite_links(content, path, selected_paths, repository)
        output = destination / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"  copied {path}")

    write_repository_index(repository, paths, destination)


def write_repositories_index(repositories: list[dict[str, str]]) -> None:
    lines = [
        "Repository documentation",
        "========================",
        "",
        "The following pages are refreshed from the public repositories during each documentation build.",
        "",
        ".. toctree::",
        "   :maxdepth: 2",
        "",
    ]
    lines.extend(f"   {repository['name']}/index" for repository in repositories)
    lines.append("")
    (OUTPUT_DIR / "index.rst").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    repositories = load_repositories()
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    failures: list[str] = []
    for repository in repositories:
        try:
            process_repository(repository)
        except Exception as error:  # Keep processing so CI reports every failed repository.
            failures.append(f"{repository['path']}: {error}")

    if failures:
        raise RuntimeError("Could not import documentation:\n" + "\n".join(failures))
    write_repositories_index(repositories)
    print(f"Imported documentation from {len(repositories)} repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
