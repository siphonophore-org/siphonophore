<img src="siphonophore/banner.svg" alt="Siphonophore: Purpose-built plugins that extend Jellyfin administration" width="100%">

# Brand

Logos and artwork for Siphonophore and its projects. Every file is an SVG, and every logo is a placeholder until the final artwork is made.

| | Project | Color | Folder |
| --- | --- | --- | --- |
| <img src="siphonophore/logo.svg" width="40"> | Siphonophore | `#0B3D4F` | [siphonophore](siphonophore) |
| <img src="necto/logo.svg" width="40"> | Necto | `#00A4DC` | [necto](necto) |
| <img src="zooid/logo.svg" width="40"> | Zooid | `#AA5CC3` | [zooid](zooid) |
| <img src="stolon/logo.svg" width="40"> | Stolon | `#6E7781` | [stolon](stolon) |

## Files

Each project folder holds its logo and the images built from it.

| File | Use |
| --- | --- |
| `logo.svg` | The square mark. It is the only file drawn by hand, and every other file is built from it. |
| `banner.svg` | The banner at the top of the project's README: its name and subtitle on a color band, over its logo. |
| `catalog.svg` | The 16:9 image the Jellyfin plugin catalog shows: the logo on the project's color. |
| `card.svg` | The project's tile on the organization profile. It follows the reader's light or dark theme. Siphonophore itself has none. |

## Changing the Artwork

1. Replace `<project>/logo.svg`. It needs a `viewBox`.
2. Change the name, subtitle, colors, or card text in [projects.json](projects.json) if they change too.
3. Run `python3 scripts/build_brand.py` to build the banner, catalog image, and card again, and commit them with the logo.

The Test workflow runs `python3 scripts/build_brand.py --check` and fails when a built file does not match its logo.

## Using It

A project's README starts with its banner:

```html
<img src="https://raw.githubusercontent.com/siphonophore-org/siphonophore/main/brand/stolon/banner.svg" alt="Stolon: Part of the Siphonophore project" width="100%">
```

Outside this repository, link to a file by its raw URL so it always shows the current artwork.
