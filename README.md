<img src="brand/siphonophore/banner.svg" alt="Siphonophore: Purpose-built plugins that extend Jellyfin administration" width="100%">

# Siphonophore

The heart of Siphonophore and its Jellyfin plugin repository.

## Installing

1. In Jellyfin, open **Dashboard > Plugins > Repositories**, select **Add Repository**, enter the URL of the channel you want and select **Save**.
2. Open the **Catalog** tab, find the plugin and select **Install**.
3. Restart Jellyfin when it asks.

### Stable

Releases that are ready for everyday use. Start here.

```
https://repo.siphonophore.org/stable
```

### Unstable

Every stable release plus test builds that are still being tried out. Test builds can break things, so keep a backup of your Jellyfin data.

```
https://repo.siphonophore.org/unstable
```

Add only one of the two. Jellyfin offers the newest version it finds across all repositories, so adding both is the same as adding Unstable.

## Plugins

| Plugin | Description |
| --- | --- |
| [Necto](https://github.com/siphonophore-org/necto) | Tools to keep your Jellyfin server reachable, secure and healthy. |
| [Zooid](https://github.com/siphonophore-org/zooid) | Keeps your whole collection of Jellyfin servers in sync with one another. |

## Releasing

Each plugin publishes its own GitHub releases. This repository turns them into the two manifests that `repo.siphonophore.org` serves.

| Channel | URL | Lists | Version |
| :--- | :--- | :--- | :--- |
| Stable | `https://repo.siphonophore.org/stable` | Every published release that is not a pre-release | `JJ.JJ.F.B`, such as `12.4.0.0` |
| Unstable | `https://repo.siphonophore.org/unstable` | Every stable release, plus every pre-release | `JJ.JJ.YYYY.N`, such as `12.4.2026.1` |

`JJ.JJ` is the Jellyfin version the release targets. An unstable version holds the year and a count that goes up by one with each unstable build, so it sorts after every stable release and after the builds before it.

### Stable Release

1. On the plugin's `unstable` branch, set `version` and the `changelog` in `build.yaml`, and push.
2. Run **Sync Branches** with `promote` from the plugin's Actions tab. It moves `main` to `unstable`. A bug fix is made on `main` instead, and the sync carries it to `unstable`.
3. Every push to `main` builds the zip into a draft release named `v<version>`. Start **Create/Update Release Draft** by hand when the push only changed `build.yaml`.
4. Open the draft, check its notes and its zip, and publish it.
5. The plugin's **Publish Plugin** workflow sends this repository a `plugin-released` event, and the stable and unstable manifests list the release.

### Unstable Release

**Release Unstable** in each plugin builds its `unstable` branch and publishes it as a pre-release.

* It runs every Friday at 15:00 UTC, and skips when nothing changed since the last unstable build.
* Start it by hand from the plugin's Actions tab to release on any other day. It takes no input.
* It takes the last unstable build's count plus one, and the count starts at 1 each year. Only published pre-releases with a zip count, so a failed run takes no number.
* It sets the version for its own build only, so `build.yaml` keeps the stable version.
* Releases are immutable once published, so it builds into a draft and publishes the draft once the zip is in.
* Its notes list the commits since the last unstable build.

### Manifests

[scripts/build_manifests.py](scripts/build_manifests.py) builds both manifests from each plugin's releases, and the [Publish workflow](.github/workflows/publish.yaml) runs it. It runs every six hours, when [plugins.json](plugins.json) changes, when a plugin sends a `plugin-released` event, and by hand from the Actions tab. A release without a zip is left out.

A plugin sends the event with this step, which needs a `SIPHONOPHORE_DISPATCH_TOKEN` secret, a fine-grained token with **Contents: Read and write** on this repository. Without it a release is listed on the next six-hourly rebuild.

```yaml
- name: Update the Siphonophore repository
  env:
    GH_TOKEN: ${{ secrets.SIPHONOPHORE_DISPATCH_TOKEN }}
  run: gh api repos/siphonophore-org/siphonophore/dispatches -f event_type=plugin-released
```

`repo.siphonophore.org` is two Cloudflare redirect rules. `/stable` sends to `manifest.json` and `/unstable` to `manifest-unstable.json` on this repository's `main` branch. GitHub caches the raw files for up to five minutes, so a release can take that long to appear.

To list a new plugin, add it to [plugins.json](plugins.json) with its repository, GUID and catalog details. Each release needs a plugin zip whose `meta.json` carries the same GUID and a `targetAbi`.

## Brand

Logos and artwork are in [brand](brand). Every banner, card, and catalog image is built from its project's logo by [scripts/build_brand.py](scripts/build_brand.py).
