---
sidebar_label: CLI Reference
---

# CLI Reference

```bash
cve-lite [path] [options]
cve-lite overrides [path] [options]
cve-lite advisories sync [options]
cve-lite advisories init [options]
cve-lite config <set|unset|show> [key] [value]
cve-lite install-skill
```

`path` defaults to the current directory if omitted.

---

## Scan options

| Flag | Default | Description | Example |
|---|---|---|---|
| `--prod-only` | off | Exclude dev dependencies from the scan | `cve-lite . --prod-only` |
| `--min-severity` | `medium` | Only show findings at or above this severity (`critical`, `high`, `medium`, `low`) | `cve-lite . --min-severity high` |
| `--all` | off | Show all findings including low and unknown; appends a full table in compact mode | `cve-lite . --all` |
| `--search-depth` | `4` | How many directory levels deep to search for a lockfile | `cve-lite . --search-depth 2` |
| `--batch-size` | `100` | Number of packages sent per OSV API request | `cve-lite . --batch-size 50` |
| `--create-pr` | off | After --fix, commit changes and open a GitHub pull request (requires `gh`) | `cve-lite --fix --create-pr` |
| `--base <branch>` | `main` | Base branch for `--create-pr` | `cve-lite --fix --create-pr --base develop` |
| `--debug` | off | Write verbose runtime/network diagnostics to a timestamped log file | `cve-lite --debug` |
---

## Output options

| Flag | Default | Description | Example |
|---|---|---|---|
| `--verbose` | off | Full output: severity table, fix plan, findings table (with EPSS and EPSS Priority columns), coverage notes | `cve-lite . --verbose` |
| `--json` | off | Machine-readable JSON output (suppresses all other output); each finding includes `epssScores` and `prioritySignal` when EPSS data is available, plus heuristic `contextualSignals` (`usage`, `reachabilityHint`, `exposure`) for prioritization — not exploitability verdicts | `cve-lite . --json` |
| `--sarif` | off | Write SARIF 2.1.0 output to a timestamped `.sarif` file; can be combined with `--json` and `--report` | `cve-lite . --sarif` |
| `--sbom <format>` | off | Write an SBOM to a timestamped file. Formats: `cyclonedx` (1.6, `.cdx.json`), `spdx` or `spdx2.3` (SPDX 2.3, `.spdx.json`). Can be combined with `--json` and `--sarif`; cannot be combined with `--report` or `--fix` | `cve-lite . --sbom spdx` |
| `--sbom-inventory-only` | off | Omit the vulnerability overlay from `--sbom`, leaving a pure inventory. Requires `--sbom` | `cve-lite . --sbom spdx --sbom-inventory-only` |
| `--cdx` | off | Alias for `--sbom cyclonedx`, kept for compatibility | `cve-lite . --cdx` |
| `--report[=<path>]` | off / `./cve-report` | Generate an HTML report with EPSS and EPSS Priority columns and an interactive priority legend; optional path sets output directory (default `./cve-report`); opens in browser by default; cannot be used with `--json` | `cve-lite . --report`<br/>`cve-lite . --report ./reports` |
| `--no-open` | off | Generate the HTML report without opening it in the browser | `cve-lite . --report --no-open` |

### EPSS Priority Signal

When EPSS data is available for a finding, CVE Lite CLI combines CVSS-derived severity with the EPSS exploitation likelihood percentile to produce a single actionable priority tier. EPSS is the [Exploit Prediction Scoring System](https://www.first.org/epss/) from FIRST.org - it scores how likely a CVE is to be exploited in the next 30 days relative to all published CVEs.

| Tier | Condition | Meaning |
|---|---|---|
| `fix_now` | Critical or high severity + EPSS top 10% | High impact and actively exploited class of CVE - address immediately |
| `fix_soon` | Critical or high severity, EPSS not top 10% | High impact but exploitation is less common - schedule a fix |
| `monitor` | Medium or lower severity, EPSS top 10% | Lower impact but exploitation is active - watch closely |
| `low_priority` | Medium or lower severity, EPSS not top 10% | Address in normal maintenance cycle |

The tier is `null` in JSON output when no EPSS data is available for a finding (typically when a finding has no CVE alias that resolves against the FIRST.org API). In terminal and HTML output, those cells show `-`.

In terminal compact mode, only `fix_now` findings are flagged inline with `⚡ Fix Now`. In verbose mode and the HTML report, all four tiers appear in a dedicated EPSS Priority column alongside the raw EPSS percentile.

`contextualSignals` is a separate JSON field (also printed in verbose terminal output). It is a heuristic prioritization hint from import scans and lockfile path names, not an EPSS tier and not an exploitability verdict. See [Reading the Output](./reading-output.md#prioritization-signals-heuristic).

---

## Offline options

| Flag | Default | Description | Example |
|---|---|---|---|
| `--offline` | off | Use the local advisory DB only — no external advisory API calls | `cve-lite . --offline` |
| `--offline-db=<path>` | auto | Path to a specific advisory DB file | `cve-lite . --offline-db ./advisories.db` |

Sync the local advisory DB with:

```bash
cve-lite advisories sync
cve-lite advisories sync --output ./advisories.db   # write to a specific path
```

In air-gapped environments that cannot reach OSV, create an empty DB and populate it from your own advisory sources instead:

```bash
cve-lite advisories init
cve-lite advisories init --output ./advisories.db   # create at a specific path
```

`advisories init` refuses to overwrite an existing file, so point `--output` at a fresh path.

See [Offline Advisory DB](./offline-advisory-db.md) for the full offline workflow.

---

## Network / SSL options

| Flag | Default | Description | Example |
|---|---|---|---|
| `--ca-cert=<path>` | - | Path to a PEM CA certificate file for corporate SSL inspection proxies | `cve-lite . --ca-cert ~/corp-ca.crt` |
| `--osv-url=<url>` | OSV API | Use a custom OSV-compatible endpoint instead of the public API (HTTPS only, public IPs only by default) | `cve-lite . --osv-url https://osv.example.com` |
| `--allow-private-osv-url` | off | Allow `--osv-url` to resolve to private/reserved IPs (RFC 1918, loopback, link-local) for internal mirrors | `cve-lite . --osv-url https://internal-mirror.local/osv --allow-private-osv-url` |

**Security note:** The `--osv-url` flag enforces HTTPS and blocks private/reserved IP ranges by default to prevent SSRF attacks. Use `--allow-private-osv-url` only when connecting to trusted internal mirrors.

For networks with SSL inspection, save the certificate path once so you do not need to pass the flag on every scan:

```bash
cve-lite config set ca-cert /path/to/corporate-ca.crt
```

See [Corporate SSL Proxy](./corporate-proxy.md) for the full setup workflow.

---

## CI / Automation options

| Flag | Default | Description | Example |
|---|---|---|---|
| `--fail-on` | `critical` | Exit with code `1` if any finding meets or exceeds this severity (`critical`, `high`, `medium`, `low`); exit `0` otherwise | `cve-lite . --fail-on high` |
| `--incomplete-policy` | `warn` | How to handle incomplete scan data: `warn` (default) prints diagnostics but exits based on findings; `error` exits with code `3` when detection data is incomplete | `cve-lite . --incomplete-policy error` |
| `--ratchet` | off | Save current CVE findings as a baseline, or if a baseline exists, only fail on findings above it. In multi-folder mode each subfolder gets its own `.cve-lite/baseline.json` | `cve-lite . --ratchet` |
| `--fix` | off | Auto-apply direct-dependency fix commands (direct deps only, v1); cannot be used with `--json`, `--sarif`, or `--sbom`/`--cdx` | `cve-lite . --fix` |
| `--check-overrides` | off | Audit `overrides` and `resolutions` entries as part of the scan (OA001-OA008); results appear in the scan output | `cve-lite . --check-overrides` |
| `--check-maintenance` | off | Run maintenance risk checks alongside the CVE scan (DM001); surfaces dependency drag and checks for deprecated packages | `cve-lite . --check-maintenance` |
| `--usage` | off | Scan source files to detect which packages are actually imported | `cve-lite . --usage` |
| `--only-used` | off | Show only findings for packages that are imported in source code (implies `--usage`) | `cve-lite . --only-used` |

**Note:** `--usage-hints` is a deprecated alias for `--usage`.

See [Workflow Integration](./workflow-integration.md) for CI/CD patterns and GitHub Actions templates.

---

## Override hygiene options

`--check-overrides` adds override auditing to a regular scan. For a dedicated override-only run, use the `overrides` subcommand:

```bash
cve-lite overrides [path] [options]
```

`path` defaults to the current directory if omitted.

| Flag | Default | Description | Example |
|---|---|---|---|
| `--check-network` | off | Enable network checks for OA007 (frozen latest) | `cve-lite overrides . --check-network` |
| `--fix` | off | Auto-fix override issues where possible | `cve-lite overrides . --fix` |
| `--json` | off | Machine-readable JSON output | `cve-lite overrides . --json` |
| `--rule=<id>` | all | Run only a specific rule (e.g. `OA001`, `OA007`) | `cve-lite overrides . --rule=OA007` |
| `--fail-on` | off | Exit with code `1` if any override finding is at or above this severity | `cve-lite overrides . --fail-on high` |
| `--audit-log=<path>` | - | Write a JSONL audit log of all findings to the specified path | `cve-lite overrides . --audit-log ./overrides.jsonl` |

See the [Override Hygiene Auditing guide](./override-hygiene/index.md) for the full rule reference (OA001-OA008), per-rule examples, and CI patterns.

---

## Maintenance risk options

### `--check-maintenance`

Run maintenance risk checks alongside the CVE scan (rule DM001). Surfaces direct dependencies that block a transitive CVE fix via a major-version constraint drag (`high`), and direct dependencies that are deprecated on npm (`medium`), even ones that are not blocking a fix. When a flagged package's latest release is over two years old, a `Last release` context line is added; release age does not change severity on its own.

When online, this fetches one npm packument per direct dependency (bounded concurrency, cached) to check for deprecation and read the last-release date. With `--offline`, the deprecation and release-age checks are skipped and only drag findings surface.

```bash
cve-lite . --check-maintenance
cve-lite . --check-maintenance --fail-on high
cve-lite . --check-maintenance --offline
cve-lite . --check-maintenance --json
```

---

## License scanning options

### `--check-licenses`

Scan dependencies for copyleft and unknown licenses alongside the CVE scan. Always informational - license findings never affect exit code.

**Rules:**
- **LC001** (`high`) - Copyleft license (GPL, AGPL, LGPL): using this dependency in commercial software may require open-sourcing your code.
- **LC002** (`medium`) - No license declared: the dependency has no `license` field, uses `UNLICENSED`, or defers to a file. Legally ambiguous - treat as proprietary until verified.

For npm projects, license data is read directly from `package-lock.json` (no network calls, works offline). For pnpm, Yarn, and Bun projects, only direct dependencies are checked (transitive license data requires registry calls not yet implemented for non-npm lockfiles).

```bash
cve-lite . --check-licenses
cve-lite . --check-licenses --json
cve-lite . --check-licenses --sarif
```

---

## Cache options

| Flag | Default | Description | Example |
|---|---|---|---|
| `--cache-dir=<path>` | `~/.cache/cve-lite` | Use a specific directory for the advisory response cache | `cve-lite . --cache-dir ./.cache` |
| `--no-cache` | — | Skip the query cache and fetch fresh results from OSV and the npm registry advisory API for this scan | `cve-lite . --no-cache` |

To clear the cache manually, delete `~/.cache/cve-lite/osv-vulns.json`. The next scan will re-fetch advisories from all sources.

Query cache entries expire after 30 minutes. Use `--no-cache` to force a fresh query immediately without waiting for the TTL. See the [Caching guide](./caching.md) for full details including false negative and false positive risk.

---

## Other commands

### `config`

```bash
cve-lite config set ca-cert <path>   # Save a CA certificate path
cve-lite config unset ca-cert        # Remove the saved CA certificate path
cve-lite config show                 # Print current config and config file location
```

Manages persistent CLI configuration stored in `~/.cve-lite-cli/config.json`. Currently supports one key:

| Key | Description |
|---|---|
| `ca-cert` | Path to a PEM CA certificate for corporate SSL inspection proxies |

The file must be a valid PEM certificate (starting with `-----BEGIN CERTIFICATE-----`). CVE Lite CLI validates the file exists and is readable before saving.

See [Corporate SSL Proxy](./corporate-proxy.md) for the full workflow.

---

### `install-skill`

```bash
cve-lite install-skill
```

Writes AI assistant skill files into the current project directory for Claude Code, Codex CLI, Gemini CLI, Cursor, and GitHub Copilot. Commit the generated files to share them with your team.

See the [AI Assistant Integration guide](./ai-assistant-integration.md) for the full workflow.
