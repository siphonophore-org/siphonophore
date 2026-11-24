<img src="brand/siphonophore/logo.svg" alt="Siphonophore" width="96" align="left">

# Siphonophore

The heart of Siphonophore and its Jellyfin plugin repository.

<br clear="left">

## Installing

1. In Jellyfin, open **Dashboard > Plugins > Repositories**, select **Add Repository**, enter the URL of the channel you want and select **Save**.
2. Open the **Catalog** tab, find the plugin and select **Install**.
3. Restart Jellyfin when it asks.

### Stable

Releases that are ready for everyday use. Start here.

```
https://raw.githubusercontent.com/siphonophore-org/siphonophore/main/manifest.json
```

### Unstable

Every stable release plus test builds that are still being tried out. Test builds can break things, so keep a backup of your Jellyfin data.

```
https://raw.githubusercontent.com/siphonophore-org/siphonophore/main/manifest-unstable.json
```

Add only one of the two. Jellyfin offers the newest version it finds across all repositories, so adding both is the same as adding Unstable.

## Plugins

| Plugin | Description |
| --- | --- |
| [Necto](https://github.com/siphonophore-org/necto) | Tools to keep your Jellyfin server reachable, secure and healthy. |
| [Zooid](https://github.com/siphonophore-org/zooid) | Keeps your whole collection of Jellyfin servers in sync with one another. |

## Publishing

Both manifests are built from each plugin's GitHub releases by [scripts/build_manifests.py](scripts/build_manifests.py). A release marked as a pre-release goes in Unstable only. Every other release goes in both.

The [Publish workflow](.github/workflows/publish.yaml) rebuilds them every six hours, when [plugins.json](plugins.json) changes, and when a plugin repository sends a `plugin-released` event:

```yaml
- name: Update the Siphonophore repository
  env:
    GH_TOKEN: ${{ secrets.SIPHONOPHORE_DISPATCH_TOKEN }}
  run: gh api repos/siphonophore-org/siphonophore/dispatches -f event_type=plugin-released
```

`SIPHONOPHORE_DISPATCH_TOKEN` is a fine-grained token with **Contents: Read and write** on this repository.

To list a new plugin, add it to [plugins.json](plugins.json) with its repository, GUID and catalog details. Each release needs a plugin zip whose `meta.json` carries the same GUID and a `targetAbi`.

## Brand

Logos and artwork are in [brand](brand).
