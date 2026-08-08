# update_from_github.py
"""Utility to fetch selected files from a GitHub repository and overwrite them on the Pico.
It uses a manifest JSON that lists the relative paths of files to update.
Only files listed in the manifest are overwritten; all other files (e.g., boot.py, settings.toml)
remain untouched, preserving developer‑editable data and sensitive credentials.
"""
import os
import json
import gc

# Import the appropriate request library for CircuitPython
try:
    import adafruit_requests as requests  # type: ignore
except ImportError:
    import urequests as requests  # type: ignore

def _download_file(raw_url):
    """Download a file from the given raw GitHub URL and return its content as bytes."""
    resp = requests.get(raw_url)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to download {raw_url}: HTTP {resp.status_code}")
    content = resp.content
    resp.close()
    return content

def run_update(settings):
    """Perform OTA update based on the provided *settings* dict.
    Expected keys in *settings*:
        - manifest_url: URL to the manifest JSON (raw GitHub link)
        - github_username, github_repo, github_branch: Repository details (used to build raw URLs)
        - excluded_files: list of file paths (relative to the project root) that must NOT be overwritten
    """
    manifest_url = settings.get("manifest_url")
    if not manifest_url:
        print("[GitHub OTA] No manifest URL configured – skipping update.")
        return

    # Download manifest JSON
    try:
        manifest_raw = _download_file(manifest_url)
        manifest = json.loads(manifest_raw)
    except Exception as e:
        print(f"[GitHub OTA] Failed to fetch manifest: {e}")
        return

    files = manifest.get("files", [])
    if not files:
        print("[GitHub OTA] Manifest contains no files – nothing to update.")
        return

    base_raw_url = (
        f"https://raw.githubusercontent.com/"
        f"{settings.get('github_username')}/{settings.get('github_repo')}/{settings.get('github_branch')}/"
    )
    excluded = set(settings.get("excluded_files", []))

    for rel_path in files:
        # Skip excluded files
        if rel_path in excluded:
            print(f"[GitHub OTA] Skipping excluded file: {rel_path}")
            continue
        raw_url = base_raw_url + rel_path
        try:
            content = _download_file(raw_url)
            # Write content to the local filesystem (CIRCUITPY root)
            with open(rel_path, "wb") as f:
                f.write(content)
            print(f"[GitHub OTA] Updated {rel_path}")
            # Run a tiny GC to keep RAM usage low between files
            gc.collect()
        except Exception as e:
            print(f"[GitHub OTA] Error updating {rel_path}: {e}")

    print("[GitHub OTA] Update routine completed.")
