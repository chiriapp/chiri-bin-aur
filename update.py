#!/usr/bin/env python3
import sys
import re
import urllib.request

if len(sys.argv) < 2:
    print("Usage: ./update.py <version> (e.g., 0.9.0)")
    sys.exit(1)

version = sys.argv[1].lstrip('v')
print(f"Updating package to v{version}...")

def get_sha256sum(url):
    print(f"Downloading {url} to compute sha256...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            import hashlib
            h = hashlib.sha256()
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk: break
                h.update(chunk)
            return h.hexdigest()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return "SKIP"

def update_file(filepath, replacements):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        for pattern, repl in replacements:
            content = re.sub(pattern, repl, content, flags=re.MULTILINE)
        with open(filepath, 'w') as f:
            f.write(content)
    except FileNotFoundError:
        print(f"File not found: {filepath}")

amd64_url = f"https://github.com/chiriapp/chiri/releases/download/app-v{version}/Chiri_{version}_amd64.deb"
arm64_url = f"https://github.com/chiriapp/chiri/releases/download/app-v{version}/Chiri_{version}_arm64.deb"

amd64_sum = get_sha256sum(amd64_url)
arm64_sum = get_sha256sum(arm64_url)

update_file("PKGBUILD", [
    (r"^pkgver=.*", f"pkgver={version}"),
    (r"^pkgrel=.*", "pkgrel=1"),
    (r"sha256sums_x86_64=\(\n  '[^']+'", f"sha256sums_x86_64=(\n  '{amd64_sum}'"),
    (r"sha256sums_aarch64=\(\n  '[^']+'", f"sha256sums_aarch64=(\n  '{arm64_sum}'")
])

try:
    with open('.SRCINFO', 'r') as f:
        lines = f.readlines()
    new_lines = []
    x86_sha_count = 0
    aarch_sha_count = 0
    for line in lines:
        if line.strip().startswith('pkgver = '): line = f"\tpkgver = {version}\n"
        elif line.strip().startswith('pkgrel = '): line = "\tpkgrel = 1\n"
        elif line.strip().startswith('source_x86_64 = https://github.com/chiriapp'): line = f"\tsource_x86_64 = https://github.com/chiriapp/chiri/releases/download/app-v{version}/Chiri_{version}_amd64.deb\n"
        elif line.strip().startswith('source_aarch64 = https://github.com/chiriapp'): line = f"\tsource_aarch64 = https://github.com/chiriapp/chiri/releases/download/app-v{version}/Chiri_{version}_arm64.deb\n"
        elif line.strip().startswith('sha256sums_x86_64 ='):
            if x86_sha_count == 0: line = f"\tsha256sums_x86_64 = {amd64_sum}\n"
            x86_sha_count += 1
        elif line.strip().startswith('sha256sums_aarch64 ='):
            if aarch_sha_count == 0: line = f"\tsha256sums_aarch64 = {arm64_sum}\n"
            aarch_sha_count += 1
        new_lines.append(line)

    with open('.SRCINFO', 'w') as f:
        f.writelines(new_lines)
except FileNotFoundError:
    print("File not found: .SRCINFO")

print("==> Done!")
