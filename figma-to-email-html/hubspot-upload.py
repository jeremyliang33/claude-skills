#!/usr/bin/env python3
"""
HubSpot Image Uploader
Uploads images from URLs (e.g. Figma asset exports) to HubSpot File Manager.

Usage:
  python3 hubspot-upload.py                          # interactive mode
  python3 hubspot-upload.py --urls url1 url2 ...     # pass URLs directly
  python3 hubspot-upload.py --folder "my/folder"     # set folder path
  python3 hubspot-upload.py --env /path/to/env.txt   # specify env file
"""

import os
import sys
import json
import argparse
import requests
from urllib.parse import urlparse, unquote
from pathlib import Path


# ── Config ──────────────────────────────────────────────────────────────────

DEFAULT_ENV_PATHS = [
    Path.home() / "Downloads" / "env.txt",
    Path(".env"),
    Path(".env.local"),
]

HUBSPOT_UPLOAD_URL = "https://api.hubapi.com/files/v3/files"


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_token(env_path=None):
    """Read HUBSPOT_ACCESS_TOKEN from env file or environment."""
    # 1. Explicit path
    if env_path:
        token = parse_env_file(env_path)
        if token:
            return token
        print(f"⚠️  Could not find token in {env_path}")

    # 2. Check default locations
    for path in DEFAULT_ENV_PATHS:
        if path.exists():
            token = parse_env_file(path)
            if token:
                print(f"✅ Loaded token from {path}")
                return token

    # 3. System environment
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")
    if token:
        return token

    print("❌ No HubSpot token found. Set HUBSPOT_ACCESS_TOKEN in your env file.")
    sys.exit(1)


def parse_env_file(path):
    """Extract HUBSPOT_ACCESS_TOKEN value from a key=value env file."""
    try:
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if line.startswith("HUBSPOT_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip()
    except Exception as e:
        print(f"⚠️  Could not read {path}: {e}")
    return None


def filename_from_url(url):
    """Derive a clean filename from a URL, URL-decoding percent-encoding."""
    raw = urlparse(url).path.split("/")[-1]
    return unquote(raw)


def download(url):
    """Download a file from a URL, return (bytes, content_type)."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    content_type = r.headers.get("Content-Type", "application/octet-stream").split(";")[0]
    return r.content, content_type


def upload_to_hubspot(token, file_bytes, filename, content_type, folder_path):
    """Upload a file to HubSpot File Manager. Returns the file object dict."""
    options = json.dumps({"access": "PUBLIC_INDEXABLE", "overwrite": True})
    response = requests.post(
        HUBSPOT_UPLOAD_URL,
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, file_bytes, content_type)},
        data={"folderPath": folder_path, "options": options},
        timeout=60,
    )
    if not response.ok:
        raise RuntimeError(f"Upload failed ({response.status_code}): {response.text}")
    return response.json()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Upload images to HubSpot File Manager")
    parser.add_argument("--urls", nargs="+", help="Image URLs to upload")
    parser.add_argument("--folder", help="HubSpot destination folder path")
    parser.add_argument("--env", help="Path to env file containing HUBSPOT_ACCESS_TOKEN")
    args = parser.parse_args()

    token = load_token(args.env)

    # ── Collect URLs ──────────────────────────────────────────────────────────
    urls = args.urls
    if not urls:
        print("\n📎 Paste image URLs (one per line). Enter a blank line when done:")
        urls = []
        while True:
            line = input("  URL: ").strip()
            if not line:
                break
            urls.append(line)

    if not urls:
        print("No URLs provided. Exiting.")
        sys.exit(0)

    # Show detected filenames
    filenames = [filename_from_url(u) for u in urls]
    print("\n🖼  Detected filenames:")
    for fn in filenames:
        print(f"  • {fn}")

    # ── Folder path ───────────────────────────────────────────────────────────
    folder_path = args.folder
    if not folder_path:
        print("\n📁 Enter HubSpot destination folder path")
        print("   (e.g. email-assets/2026/Q1/campaign-name)")
        folder_path = input("  Folder: ").strip()

    if not folder_path:
        print("No folder provided. Exiting.")
        sys.exit(0)

    # ── Upload ────────────────────────────────────────────────────────────────
    print(f"\n⬆️  Uploading {len(urls)} file(s) to /{folder_path} ...\n")
    results = []

    for url, filename in zip(urls, filenames):
        try:
            print(f"  Downloading {filename} ...", end=" ", flush=True)
            file_bytes, content_type = download(url)
            print(f"({len(file_bytes) // 1024}KB)", end=" ", flush=True)

            print(f"→ uploading ...", end=" ", flush=True)
            result = upload_to_hubspot(token, file_bytes, filename, content_type, folder_path)

            hs_url = result.get("url", "")
            print(f"✅")
            print(f"     HubSpot URL: {hs_url}")
            results.append({"filename": filename, "hubspot_url": hs_url, "id": result.get("id")})

        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({"filename": filename, "error": str(e)})

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n─────────────────────────────────────────")
    print("📋 Upload Summary\n")
    for r in results:
        if "error" in r:
            print(f"  ❌ {r['filename']}: {r['error']}")
        else:
            print(f"  ✅ {r['filename']}")
            print(f"     {r['hubspot_url']}")
    print()


if __name__ == "__main__":
    main()
