import hashlib
import io
import json
import unittest
import zipfile
from unittest import mock

import build_manifests as bm

PLUGIN = {
    "repo": "siphonophore-org/example",
    "guid": "11111111-2222-3333-4444-555555555555",
    "name": "Example",
    "overview": "An example.",
    "description": "An example plugin.",
    "category": "Administration",
    "imageUrl": "https://example.invalid/logo.png",
}


def plugin_zip(version, guid=PLUGIN["guid"], abi="12.4.0.0"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("meta.json", json.dumps({"guid": guid, "version": version, "targetAbi": abi}))
        archive.writestr("Example.dll", b"dll")
    return buffer.getvalue()


def release(tag, prerelease=False, published="2026-11-01T00:00:00Z", body="Notes"):
    name = f"example-{tag.lstrip('v')}.zip"
    return {
        "tag_name": tag,
        "prerelease": prerelease,
        "published_at": published,
        "body": body,
        "assets": [
            {
                "name": name,
                "url": f"api/{name}",
                "browser_download_url": f"https://example.invalid/{name}",
                "updated_at": published,
            }
        ],
    }


class BuildTests(unittest.TestCase):
    def run_build(self, releases, zips, cache=None):
        def fake_request(url, accept=None):
            return zips[url.split("/", 1)[1]]

        with mock.patch.object(bm, "request", side_effect=fake_request):
            return bm.build([PLUGIN], lambda repo: releases, {} if cache is None else cache)

    def test_prereleases_go_only_in_unstable(self):
        zips = {"example-1.0.0.0.zip": plugin_zip("1.0.0.0"), "example-1.1.0.0.zip": plugin_zip("1.1.0.0")}
        stable, unstable = self.run_build([release("v1.0.0.0"), release("v1.1.0.0", prerelease=True)], zips)

        self.assertEqual([v["version"] for v in stable[0]["versions"]], ["1.0.0.0"])
        self.assertEqual([v["version"] for v in unstable[0]["versions"]], ["1.1.0.0", "1.0.0.0"])

    def test_versions_sort_by_number_not_text(self):
        zips = {"example-1.0.9.0.zip": plugin_zip("1.0.9.0"), "example-1.0.10.0.zip": plugin_zip("1.0.10.0")}
        stable, _ = self.run_build([release("v1.0.9.0"), release("v1.0.10.0")], zips)

        self.assertEqual([v["version"] for v in stable[0]["versions"]], ["1.0.10.0", "1.0.9.0"])

    def test_checksum_is_the_zip_md5(self):
        data = plugin_zip("1.0.0.0")
        stable, _ = self.run_build([release("v1.0.0.0")], {"example-1.0.0.0.zip": data})

        self.assertEqual(stable[0]["versions"][0]["checksum"], hashlib.md5(data).hexdigest())
        self.assertEqual(stable[0]["versions"][0]["targetAbi"], "12.4.0.0")

    def test_a_zip_for_another_plugin_is_left_out(self):
        zips = {"example-1.0.0.0.zip": plugin_zip("1.0.0.0", guid="99999999-0000-0000-0000-000000000000")}
        stable, unstable = self.run_build([release("v1.0.0.0")], zips)

        self.assertEqual(stable, [])
        self.assertEqual(unstable, [])

    def test_a_plugin_with_only_prereleases_is_not_in_stable(self):
        zips = {"example-1.0.0.0.zip": plugin_zip("1.0.0.0")}
        stable, unstable = self.run_build([release("v1.0.0.0", prerelease=True)], zips)

        self.assertEqual(stable, [])
        self.assertEqual(unstable[0]["owner"], "siphonophore")

    def test_an_unchanged_zip_comes_from_the_cache(self):
        cache = {
            "https://example.invalid/example-1.0.0.0.zip": {
                "updated": "2026-11-01T00:00:00Z",
                "checksum": "0" * 32,
                "guid": PLUGIN["guid"],
                "version": "1.0.0.0",
                "targetAbi": "12.4.0.0",
            }
        }
        stable, _ = self.run_build([release("v1.0.0.0")], {}, cache)

        self.assertEqual(stable[0]["versions"][0]["checksum"], "0" * 32)

    def test_a_mismatched_md5_file_leaves_the_release_out(self):
        rel = release("v1.0.0.0")
        rel["assets"].append({"name": "example-1.0.0.0.zip.md5", "url": "api/example-1.0.0.0.zip.md5"})
        zips = {"example-1.0.0.0.zip": plugin_zip("1.0.0.0"), "example-1.0.0.0.zip.md5": b"ffffffffffffffffffffffffffffffff  x.zip"}
        stable, _ = self.run_build([rel], zips)

        self.assertEqual(stable, [])


if __name__ == "__main__":
    unittest.main()
