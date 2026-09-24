#!/usr/bin/env python3
"""Rough token count and price estimate for licensing a private codebase.

Usage:
    python3 estimate.py <path-to-local-repo> [--history-tokens-from-git]
                        [--exclude DIR ...] [--source-rate N] [--history-rate N]

Standard library only. The numbers are estimates, not quotes.

Method
- Walks the tree without following symlinks.
- Skips dependency, build and tool directories (node_modules, vendor, dist,
  build, target, Pods, .git, virtualenvs, caches), lockfiles, LICENSE/COPYING
  files, minified bundles and source maps, and binary or data files (images,
  fonts, archives, media, databases, model weights, logs, CSV dumps). A file
  with a NUL byte in its first 8 KiB is treated as binary.
- Sums the bytes of every remaining file and groups them by extension.
- Converts bytes to tokens at 4 bytes per token. This is an approximation.
  Real tokenizers differ by language and style, often by 20 to 30 percent.
- With --history-tokens-from-git, streams `git log -p` for the repository
  (same directory exclusions as pathspecs) and converts its byte size to
  tokens at the same ratio.
- Prices at $100 per million source tokens and $40 per million history
  tokens (override with --source-rate and --history-rate).

Copyleft check
- Scans LICENSE, LICENCE, COPYING and similar files anywhere in the tree,
  including vendor/ and third_party/ (vendored code ships with the repo),
  but not inside installed dependency folders such as node_modules.
- Scans declared license fields in package.json, composer.json,
  pyproject.toml, setup.cfg, setup.py, Cargo.toml and *.gemspec.
- Looks for GPL, AGPL, LGPL, MPL and EUPL. Any hit prints a WARN line.
- It does NOT resolve dependency licenses. Dependencies listed in
  package.json, pyproject.toml, setup.cfg, requirements files, Cargo.toml
  and go.mod are not looked up. Use a real license scanner for that.

Exit codes: 0 ok, 2 copyleft warning found, 1 usage or input error.
"""

import argparse
import json
import os
import re
import subprocess
import sys

BYTES_PER_TOKEN = 4
DEFAULT_SOURCE_RATE = 100.0   # USD per million tokens of source at head
DEFAULT_HISTORY_RATE = 40.0   # USD per million tokens of git history

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "bower_components", "jspm_packages",
    "vendor", "third_party", "third-party", "dist", "build", "target",
    "Pods", "Carthage", ".venv", "venv", ".tox", "site-packages",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".next",
    ".nuxt", ".svelte-kit", ".turbo", ".parcel-cache", ".gradle", ".idea",
    ".vscode", "coverage", ".nyc_output", "DerivedData",
}

# Directories that hold installed dependencies rather than committed code.
# The license scan skips only these (plus VCS folders), so vendored code is checked.
LICENSE_SCAN_SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "bower_components", "jspm_packages",
    ".venv", "venv", ".tox", "site-packages", "__pycache__", "Pods",
    "Carthage", "dist", "build", "target",
}

LOCKFILES = {
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
    "bun.lockb", "bun.lock", "Cargo.lock", "poetry.lock", "Pipfile.lock",
    "uv.lock", "pdm.lock", "Gemfile.lock", "composer.lock", "go.sum",
    "mix.lock", "pubspec.lock", "Podfile.lock", "packages.lock.json",
    "flake.lock",
}

BINARY_OR_DATA_EXT = {
    # images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".icns", ".webp", ".avif",
    ".tif", ".tiff", ".psd", ".ai", ".sketch", ".fig", ".heic",
    # fonts
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # archives and binaries
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar", ".jar",
    ".war", ".exe", ".dll", ".so", ".dylib", ".a", ".o", ".obj", ".class",
    ".pyc", ".pyo", ".wasm", ".bin", ".dmg", ".iso", ".apk", ".ipa",
    # media and documents
    ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".webm", ".wav", ".flac", ".ogg",
    ".m4a", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # data, weights, logs
    ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".parquet", ".feather",
    ".npy", ".npz", ".pkl", ".pickle", ".h5", ".hdf5", ".onnx", ".pt", ".pth",
    ".ckpt", ".safetensors", ".gguf", ".log", ".csv", ".tsv", ".jsonl",
    ".ndjson", ".map",
}

LICENSE_NAME_RE = re.compile(
    r"^(licen[cs]e|copying|unlicense)"
    r"(\.(txt|md|rst|markdown|lesser|gpl|lgpl|mit|apache|bsd)|[-_][A-Za-z0-9._-]+)?$", re.I)
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
            ".kt", ".rb", ".php", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".swift",
            ".scala", ".sh", ".json", ".yml", ".yaml", ".toml", ".html", ".css"}


def is_license_file(name):
    return bool(LICENSE_NAME_RE.match(name)) and \
        os.path.splitext(name)[1].lower() not in CODE_EXT

MANIFESTS = {"package.json", "composer.json", "pyproject.toml", "setup.cfg",
             "setup.py", "Cargo.toml"}

COPYLEFT_PATTERNS = [
    ("AGPL", re.compile(r"\bAGPL\b|\bAGPL-?[0-9]|GNU\s+AFFERO\s+GENERAL\s+PUBLIC\s+LICEN[CS]E", re.I)),
    ("LGPL", re.compile(r"\bLGPL\b|\bLGPL-?[0-9]|GNU\s+(LESSER|LIBRARY)\s+GENERAL\s+PUBLIC\s+LICEN[CS]E", re.I)),
    ("GPL", re.compile(r"\bGPL\b|\bGPL-?[0-9]|GNU\s+GENERAL\s+PUBLIC\s+LICEN[CS]E", re.I)),
    ("MPL", re.compile(r"\bMPL\b|\bMPL-?[0-9]|Mozilla\s+Public\s+Licen[cs]e", re.I)),
    ("EUPL", re.compile(r"\bEUPL\b|\bEUPL-?[0-9]|European\s+Union\s+Public\s+Licen[cs]e", re.I)),
]


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("error: %s\n" % message)
        sys.exit(1)


def bytes_to_tokens(n_bytes):
    return n_bytes // BYTES_PER_TOKEN


def price(source_tokens, history_tokens, source_rate=DEFAULT_SOURCE_RATE,
          history_rate=DEFAULT_HISTORY_RATE):
    """Return (source_usd, history_usd, total_usd)."""
    s = source_tokens / 1_000_000 * source_rate
    h = history_tokens / 1_000_000 * history_rate
    return s, h, s + h


def _is_binary(path):
    try:
        with open(path, "rb") as fh:
            return b"\0" in fh.read(8192)
    except OSError:
        return True


def _skip_file(name):
    lower = name.lower()
    if name in LOCKFILES or is_license_file(name):
        return True
    if lower.endswith((".min.js", ".min.css", ".bundle.js")):
        return True
    ext = os.path.splitext(lower)[1]
    return ext in BINARY_OR_DATA_EXT


def _prune(root, dirpath, dirnames, skip_names, excludes):
    """Drop skipped directory names and user-excluded relative paths in place."""
    keep = []
    for d in dirnames:
        if d in skip_names:
            continue
        rel = os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/")
        if rel in excludes:
            continue
        keep.append(d)
    dirnames[:] = keep


def _norm_excludes(excludes):
    return {e.strip("/").replace(os.sep, "/") for e in (excludes or []) if e.strip("/")}


def count_source(root, excludes=None):
    """Return (by_ext dict ext -> [files, bytes], total_bytes, skipped_files)."""
    excludes = _norm_excludes(excludes)
    by_ext = {}
    total = 0
    skipped = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        _prune(root, dirpath, dirnames, SKIP_DIRS, excludes)
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            if _skip_file(name) or _is_binary(path):
                skipped += 1
                continue
            size = os.path.getsize(path)
            ext = os.path.splitext(name)[1].lower() or "(none)"
            slot = by_ext.setdefault(ext, [0, 0])
            slot[0] += 1
            slot[1] += size
            total += size
    return by_ext, total, skipped


def git_history_bytes(root, excludes=None):
    """Byte size of `git log -p` for the repo, or None if root is not a git work tree.

    Raises RuntimeError if git log fails, for example on a repo with no commits.
    """
    try:
        check = subprocess.run(["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
                               capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if check.returncode != 0 or check.stdout.strip() != "true":
        return None
    excludes = [":(exclude,glob)**/%s/**" % d for d in sorted(SKIP_DIRS) if d != ".git"]
    user = sorted(_norm_excludes(excludes))
    pathspecs = [":(exclude,glob)**/%s/**" % d for d in sorted(SKIP_DIRS) if d != ".git"]
    pathspecs += [":(exclude,glob)**/%s" % f for f in sorted(LOCKFILES)]
    pathspecs += [":(exclude)%s" % u for u in user]
    cmd = ["git", "-C", root, "log", "-p", "--no-color", "--no-ext-diff",
           "--no-textconv", "--", "."] + pathspecs
    total = 0
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        while True:
            chunk = proc.stdout.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
        err = proc.stderr.read().decode("utf-8", "replace").strip()
    if proc.returncode != 0:
        raise RuntimeError(err.splitlines()[0] if err else "git log exit %d" % proc.returncode)
    return total


def _match_copyleft(text):
    hits = []
    for label, rx in COPYLEFT_PATTERNS:
        if rx.search(text):
            hits.append(label)
    # A GNU Affero or Lesser text also contains "GNU General Public License";
    # report only the most specific family in that case.
    if "GPL" in hits and ("AGPL" in hits or "LGPL" in hits):
        hits.remove("GPL")
    return hits


def _manifest_license_text(path, name):
    """Return only the license-declaring parts of a manifest."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError:
        return ""
    if name in ("package.json", "composer.json"):
        try:
            data = json.loads(raw)
        except ValueError:
            data = None
        if isinstance(data, dict):
            parts = []
            for key in ("license", "licenses"):
                val = data.get(key)
                if val is not None:
                    parts.append(json.dumps(val))
            return " ".join(parts)
    # TOML, cfg, setup.py, gemspec: keep lines that talk about a licence.
    lines = [ln for ln in raw.splitlines() if re.search(r"licen[cs]e", ln, re.I)]
    return "\n".join(lines)


def scan_copyleft(root, excludes=None):
    """Return a list of (relative_path, [families]) with copyleft hits."""
    excludes = _norm_excludes(excludes)
    findings = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        _prune(root, dirpath, dirnames, LICENSE_SCAN_SKIP_DIRS, excludes)
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            text = None
            if is_license_file(name):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read(200_000)
                except OSError:
                    continue
            elif name in MANIFESTS or name.endswith(".gemspec"):
                text = _manifest_license_text(path, name)
            if not text:
                continue
            hits = _match_copyleft(text)
            if hits:
                findings.append((os.path.relpath(path, root), hits))
    findings.sort()
    return findings


def main(argv=None):
    ap = _Parser(description="Estimate tokens and licensing price for a local codebase.")
    ap.add_argument("path", help="path to a local repository checkout")
    ap.add_argument("--history-tokens-from-git", action="store_true",
                    help="also estimate git history tokens from `git log -p` byte size")
    ap.add_argument("--source-rate", type=float, default=DEFAULT_SOURCE_RATE,
                    help="USD per million source tokens (default 100)")
    ap.add_argument("--history-rate", type=float, default=DEFAULT_HISTORY_RATE,
                    help="USD per million history tokens (default 40)")
    ap.add_argument("--exclude", action="append", default=[], metavar="DIR",
                    help="directory to leave out, relative to the repo root (repeatable)")
    ap.add_argument("--top", type=int, default=12,
                    help="how many extensions to list (default 12)")
    args = ap.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isdir(root):
        sys.stderr.write("error: not a directory: %s\n" % root)
        return 1

    by_ext, src_bytes, skipped = count_source(root, args.exclude)
    src_tokens = bytes_to_tokens(src_bytes)
    files = sum(v[0] for v in by_ext.values())

    print("repo: %s" % root)
    if args.exclude:
        print("excluded by --exclude: %s" % ", ".join(sorted(_norm_excludes(args.exclude))))
    print("files counted: %d (skipped outside excluded dirs: %d)" % (files, skipped))
    print("bytes by extension (top %d):" % args.top)
    ranked = sorted(by_ext.items(), key=lambda kv: kv[1][1], reverse=True)
    for ext, (n, b) in ranked[:args.top]:
        print("  %-12s %6d files %14s bytes" % (ext, n, format(b, ",")))
    if len(ranked) > args.top:
        rest = ranked[args.top:]
        print("  %-12s %6d files %14s bytes" % (
            "(other %d)" % len(rest), sum(v[0] for _, v in rest),
            format(sum(v[1] for _, v in rest), ",")))
    print("source bytes: %s" % format(src_bytes, ","))
    print("source tokens: %s (approximate, %d bytes per token)" % (
        format(src_tokens, ","), BYTES_PER_TOKEN))

    hist_tokens = 0
    if args.history_tokens_from_git:
        try:
            hb = git_history_bytes(root, args.exclude)
        except RuntimeError as exc:
            hb = None
            print("history: git log failed (%s), history tokens set to 0" % exc)
        else:
            if hb is None:
                print("history: not a git work tree, history tokens set to 0")
        if hb is not None:
            hist_tokens = bytes_to_tokens(hb)
            print("history bytes (git log -p): %s" % format(hb, ","))
            print("history tokens: %s (approximate, %d bytes per token)" % (
                format(hist_tokens, ","), BYTES_PER_TOKEN))
    else:
        print("history: not estimated (pass --history-tokens-from-git)")

    s, h, t = price(src_tokens, hist_tokens, args.source_rate, args.history_rate)
    print("price: source $%s at $%g/M + history $%s at $%g/M = $%s" % (
        format(round(s, 2), ",.2f"), args.source_rate,
        format(round(h, 2), ",.2f"), args.history_rate,
        format(round(t, 2), ",.2f")))
    print("note: published indicative rates, not a quote; buyers grade and may pay more or less")

    findings = scan_copyleft(root, args.exclude)
    for rel, fams in findings:
        print("WARN copyleft %s in %s" % ("/".join(fams), rel))
    print("note: dependency licenses are not resolved; dependencies in package.json, "
          "pyproject.toml, setup.cfg, requirements files, Cargo.toml and go.mod are not scanned")
    if findings:
        print("result: %d copyleft warning(s), exit 2" % len(findings))
        return 2
    print("result: no copyleft strings found in LICENSE files or declared license fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
