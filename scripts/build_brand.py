"""Builds every brand image from each project's logo, so a new logo reaches every banner, card, and catalog image.

brand/projects.json lists the projects. For each one, brand/<key>/logo.svg is the source. This writes:

* banner.svg, the wide banner at the top of the project's README: its name and subtitle on a color band, over its logo
* catalog.svg, the 16:9 image the Jellyfin plugin catalog shows: the logo on the project's color
* card.svg, for a project with a card: its tile on the organization profile, in the reader's light or dark theme

Run it after changing a logo or projects.json. With --check it changes nothing and fails when a built file is stale.
"""

import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = os.path.join(ROOT, "brand")
FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'


def read_logo(key):
    """The logo's viewBox and its inner markup, ready to nest inside another SVG."""
    with open(os.path.join(BRAND, key, "logo.svg"), encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r"<svg\b([^>]*)>(.*)</svg>", text, re.S)
    if not match:
        raise ValueError(f"brand/{key}/logo.svg has no <svg> element")
    attrs, inner = match.groups()
    view = re.search(r'viewBox="([^"]+)"', attrs)
    if not view:
        raise ValueError(f"brand/{key}/logo.svg needs a viewBox")
    return view.group(1), inner.strip()


def nest(key, x, y, size, prefix):
    """The logo drawn in a size by size box at x, y. Its ids take a prefix, so two copies on one page never clash."""
    view, inner = read_logo(key)
    ids = set(re.findall(r'\bid="([^"]+)"', inner))
    for name in ids:
        inner = re.sub(r'\bid="' + re.escape(name) + '"', f'id="{prefix}-{name}"', inner)
        inner = inner.replace(f"url(#{name})", f"url(#{prefix}-{name})").replace(f'href="#{name}"', f'href="#{prefix}-{name}"')
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{view}">{inner}</svg>'


def banner(project):
    """A Jellyfin style banner: the name and subtitle on a color band, and the logo centered on a dark panel below."""
    w, h, band, logo = 1200, 360, 128, 168
    start, end = project["gradient"]
    name, subtitle = html.escape(project["name"]), html.escape(project["subtitle"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{name}: {subtitle}">
  <defs>
    <linearGradient id="band" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{start}"/>
      <stop offset="1" stop-color="{end}"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{w}" height="{h}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{w}" height="{h}" fill="#0A1116"/>
    <rect width="{w}" height="{band}" fill="url(#band)"/>
    <text x="{w // 2}" y="66" text-anchor="middle" font-family='{FONT}' font-size="44" font-weight="700" fill="#ffffff">{name}</text>
    <text x="{w // 2}" y="104" text-anchor="middle" font-family='{FONT}' font-size="22" fill="#ffffff" fill-opacity="0.88">{subtitle}</text>
    {nest(project["key"], (w - logo) // 2, band + (h - band - logo) // 2, logo, "banner")}
  </g>
  <rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="15.25" fill="none" stroke="url(#band)" stroke-width="1.5"/>
</svg>
"""


def catalog(project):
    """The 16:9 catalog image: the logo, two thirds of the height, on the project's color."""
    w, h, logo = 1920, 1080, 720
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(project["name"])}">
  <rect width="{w}" height="{h}" fill="{project["color"]}"/>
  {nest(project["key"], (w - logo) // 2, (h - logo) // 2, logo, "catalog")}
</svg>
"""


CARD_STYLE = """  <style>
    .card { fill: #ffffff; stroke: #d1d9e0; }
    .name { fill: #1f2328; }
    .text { fill: #59636e; }
    @media (prefers-color-scheme: dark) {
      .card { fill: #151b23; stroke: #3d444d; }
      .name { fill: #f0f6fc; }
      .text { fill: #9198a1; }
    }
    text { font-family: """ + FONT + """; }
  </style>
"""


def card(project):
    """The profile tile. Each carries an 8px margin of its own, so tiles side by side and stacked sit 16px apart."""
    name = html.escape(project["name"])
    lines = [html.escape(line) for line in project["card"]["lines"]]
    label = f'{name}: {" ".join(lines)}'
    if project["card"]["size"] == "slim":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="872" height="104" viewBox="0 0 872 104" role="img" aria-label="{label}">
{CARD_STYLE}  <g transform="translate(8 8)">
  <rect class="card" x="0.5" y="0.5" width="855" height="87" rx="14"/>
  {nest(project["key"], 22, 22, 44, "card")}
  <text class="name" x="84" y="51" font-size="20" font-weight="600">{name}</text>
  <text class="text" x="160" y="51" font-size="15">{lines[0]}</text>
  </g>
</svg>
"""
    body = "\n".join(f'  <text class="text" x="28" y="{158 + 22 * i}" font-size="16">{line}</text>' for i, line in enumerate(lines))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="436" height="216" viewBox="0 0 436 216" role="img" aria-label="{label}">
{CARD_STYLE}  <g transform="translate(8 8)">
  <rect class="card" x="0.5" y="0.5" width="419" height="199" rx="14"/>
  {nest(project["key"], 28, 28, 56, "card")}
  <text class="name" x="28" y="128" font-size="28" font-weight="600">{name}</text>
{body}
  </g>
</svg>
"""


def outputs():
    with open(os.path.join(BRAND, "projects.json"), encoding="utf-8") as handle:
        projects = json.load(handle)
    for project in projects:
        yield os.path.join(project["key"], "banner.svg"), banner(project)
        yield os.path.join(project["key"], "catalog.svg"), catalog(project)
        if project.get("card"):
            yield os.path.join(project["key"], "card.svg"), card(project)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when a built file is stale, and write nothing")
    args = parser.parse_args()

    stale = []
    for relative, text in outputs():
        path = os.path.join(BRAND, relative)
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if current == text:
            continue
        stale.append(relative)
        if not args.check:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
    if args.check and stale:
        print("Stale brand files, run python3 scripts/build_brand.py: " + ", ".join(stale))
        return 1
    print(("Stale: " if args.check else "Wrote: ") + (", ".join(stale) if stale else "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
