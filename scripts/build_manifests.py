"""Builds the stable and unstable Jellyfin plugin manifests from each plugin's GitHub releases.

A release marked as a pre-release goes in the unstable manifest only. Every other release goes in both,
so a server on the unstable repository still gets each stable version.

Each release's zip is downloaded once and its checksum and meta.json are kept in data/assets.json. A
zip is fetched again only when GitHub reports it changed.
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER = "siphonophore"


def warn(message):
    print(f"::warning::{message}")


def request(url, accept="application/vnd.github+json"):
    headers = {"Accept": accept, "User-Agent": "siphonophore-manifest", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def releases_of(repo):
    """Every published release of a repository, or none when the repository is missing or private."""
    found = []
    page = 1
    while True:
        try:
            batch = json.loads(request(f"{API}/repos/{repo}/releases?per_page=100&page={page}"))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                warn(f"{repo} was not found or is not readable, so it has no releases to list")
                return []
            raise
        found.extend(r for r in batch if not r.get("draft"))
        if len(batch) < 100:
            return found
        page += 1


def version_key(version):
    """Sorts versions by each number in turn, so 12.4.10.0 comes after 12.4.9.0."""
    return tuple(int(part) if part.isdigit() else -1 for part in re.split(r"[.\-+]", version))


def read_meta(data):
    """The meta.json inside a plugin zip, or an empty object when it has none."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [n for n in archive.namelist() if n.rsplit("/", 1)[-1] == "meta.json"]
        if not names:
            return {}
        return json.loads(archive.read(min(names, key=len)))


def asset_info(release, asset, cache):
    """The checksum and plugin details of one release zip, from the cache when it has not changed."""
    url = asset["browser_download_url"]
    cached = cache.get(url)
    if cached and cached.get("updated") == asset["updated_at"]:
        return cached

    data = request(asset["url"], accept="application/octet-stream")
    checksum = hashlib.md5(data).hexdigest()  # Jellyfin checks plugin zips by MD5.

    sidecar = next((a for a in release["assets"] if a["name"] == asset["name"] + ".md5"), None)
    if sidecar:
        listed = request(sidecar["url"], accept="application/octet-stream").decode("utf-8", "replace").split()
        if listed and listed[0].lower() != checksum:
            raise ValueError(f"{asset['name']} hashes to {checksum} but its .md5 lists {listed[0]}")

    meta = read_meta(data)
    info = {
        "updated": asset["updated_at"],
        "checksum": checksum,
        "guid": str(meta.get("guid", "")).lower(),
        "version": str(meta.get("version", "")),
        "targetAbi": str(meta.get("targetAbi", "")),
    }
    cache[url] = info
    return info


def entries_for(plugin, releases, cache):
    """Each release of a plugin as a manifest version, with whether it is a pre-release."""
    entries = {}
    for release in releases:
        asset = next((a for a in release.get("assets", []) if a["name"].endswith(".zip")), None)
        if not asset:
            continue
        try:
            info = asset_info(release, asset, cache)
        except (ValueError, zipfile.BadZipFile, urllib.error.URLError) as error:
            warn(f"{plugin['repo']} {release['tag_name']} is left out: {error}")
            continue
        if info["guid"] and info["guid"] != plugin["guid"].lower():
            warn(f"{plugin['repo']} {release['tag_name']} is left out: its zip belongs to plugin {info['guid']}")
            continue

        version = info["version"] or release["tag_name"].lstrip("v")
        if not info["targetAbi"]:
            warn(f"{plugin['repo']} {release['tag_name']} is left out: its zip has no targetAbi")
            continue

        entry = {
            "version": version,
            "changelog": (release.get("body") or "").replace("\r\n", "\n"),
            "targetAbi": info["targetAbi"],
            "sourceUrl": asset["browser_download_url"],
            "checksum": info["checksum"],
            "timestamp": release.get("published_at") or release.get("created_at"),
        }
        # When two releases carry the same version, the later one wins.
        held = entries.get(version)
        if held is None or entry["timestamp"] > held[0]["timestamp"]:
            entries[version] = (entry, bool(release.get("prerelease")))

    return sorted(entries.values(), key=lambda pair: version_key(pair[0]["version"]), reverse=True)


def manifest_entry(plugin, versions):
    return {
        "guid": plugin["guid"],
        "name": plugin["name"],
        "overview": plugin["overview"],
        "description": plugin["description"],
        "imageUrl": plugin["imageUrl"],
        "owner": OWNER,
        "category": plugin["category"],
        "versions": versions,
    }


def build(plugins, fetch, cache):
    """Both manifests, as lists of plugins. A plugin with no versions in a channel is left out of it."""
    stable, unstable = [], []
    for plugin in plugins:
        pairs = entries_for(plugin, fetch(plugin["repo"]), cache)
        stable_versions = [entry for entry, prerelease in pairs if not prerelease]
        all_versions = [entry for entry, _ in pairs]
        if stable_versions:
            stable.append(manifest_entry(plugin, stable_versions))
        if all_versions:
            unstable.append(manifest_entry(plugin, all_versions))
    return stable, unstable


def load(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


def save(path, value):
    """Writes JSON only when it changed, so an unchanged run leaves nothing to commit."""
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            if handle.read() == text:
                return False
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=ROOT, help="the repository folder")
    args = parser.parse_args()

    plugins = load(os.path.join(args.root, "plugins.json"), [])
    cache_path = os.path.join(args.root, "data", "assets.json")
    cache = load(cache_path, {})

    stable, unstable = build(plugins, releases_of, cache)

    # Only zips still listed stay in the cache.
    listed = {v["sourceUrl"] for p in unstable for v in p["versions"]}
    cache = {url: info for url, info in cache.items() if url in listed}

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    changed = [
        name
        for name, value in (("manifest.json", stable), ("manifest-unstable.json", unstable), ("data/assets.json", cache))
        if save(os.path.join(args.root, name), value)
    ]
    for plugin in unstable:
        stable_count = next((len(p["versions"]) for p in stable if p["guid"] == plugin["guid"]), 0)
        print(f"{plugin['name']}: {stable_count} stable, {len(plugin['versions'])} in all")
    print("Changed: " + (", ".join(changed) if changed else "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
