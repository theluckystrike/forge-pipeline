import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import type { FetchLike, Finding, ParsedOptions, PackageRef, SeverityLabel, ExitCode, ScanCompleteness } from "../types.js";
import { EXIT_OK, EXIT_FINDINGS, EXIT_ERROR } from "../types.js";
import type { SuggestedFixCommandPlan } from "../remediation/fix-commands.js";
import type { ScanInput } from "../types.js";
import { loadMultiplePackages } from "../parsers/multi-package.js";
import { scanPackages, buildCoverageNotes } from "../scanner.js";
import { sortFindingsForOutput, serializeFinding, logInfo } from "../output/formatters.js";
import { resolveOutputDir, displayOutputPath } from "../output/output-dir.js";
import { normalizeSeverity } from "../osv/severity.js";
import { selectFindingsForTable } from "../output/finding-display.js";
import { buildSuggestedFixCommandPlan } from "../remediation/fix-commands.js";
import { readDirectDependencyNames, hasOverrideEntries } from "../utils/package-json.js";
import { DEFAULT_BATCH_SIZE, DEFAULT_SEARCH_DEPTH, severityOrder, OVERRIDES_COMMAND } from "../constants.js";
import { printMultiFolderResults } from "../output/multi-folder-printer.js";
import { printOverrideHint } from "../output/printers.js";
import { writeMultiFolderHtmlReport } from "../output/multi-folder-html-reporter.js";
import { chalk } from "../utils/chalk.js";
import { getCliVersion } from "../utils/version-info.js";
import { buildOverrideContext, audit } from "../overrides/index.js";
import { NULL_AUDIT_LOG, type AuditLogHandle } from "../audit-log/index.js";
import type { OverrideFinding } from "../overrides/types.js";
import { detectDM001 } from "../maintenance/dm001-maintenance-risk.js";
import type { MaintenanceFinding } from "../maintenance/types.js";
import { detectLicenseIssues } from "../licenses/license-check.js";
import { renderLicenseFindings } from "../output/license-terminal.js";
import type { LicenseFinding } from "../licenses/types.js";
import { reachesFailOn } from "../utils/severity.js";
import { readBaseline, writeBaseline, filterNewFindings, ratchetOutcome } from "../utils/baseline.js";
import { pluralize } from "../utils/string.js";
import {
  aggregateMultiFolderCompleteness,
  formatDiagnosticMessage,
  getCompletenessImpact,
  shouldFailForIncompleteScan,
} from "./completeness.js";
import { scanProjectForPackageUsage } from "../usage/scanner.js";

export interface MultiFolderScanResult {
  subfolder: string;
  scanInput: ScanInput;
  sorted: Finding[];
  suggestedFixCommands: SuggestedFixCommandPlan | null;
  coverage: string[];
  minSeverity: SeverityLabel;
  tableFindings: Finding[];
  allPackages: PackageRef[];
  completeness: ScanCompleteness;
  /** Override hygiene findings for this folder, populated when --check-overrides is set. */
  overrideFindings: OverrideFinding[];
  /** Maintenance risk (DM001) findings for this folder, populated when --check-maintenance is set. */
  maintenanceFindings: MaintenanceFinding[];
  /** License issue findings for this folder, populated when --check-licenses is set. */
  licenseFindings: LicenseFinding[];
  /** True when license data was limited to direct deps only (pnpm/Yarn/Bun). */
  licenseLimitedToDirectOnly: boolean;
  /** CVE findings suppressed by an existing per-folder baseline (non-ratchet scans). */
  suppressedCount: number;
}

export async function runMultiFolderScan(params: {
  projectRoot: string;
  batchSize: number;
  options: ParsedOptions;
  fetchImpl?: FetchLike;
  auditLog?: AuditLogHandle;
}): Promise<MultiFolderScanResult[]> {
  const searchDepth = Math.max(0, Number(params.options.searchDepth || DEFAULT_SEARCH_DEPTH));
  const folders = loadMultiplePackages(params.projectRoot, !!params.options.prodOnly, searchDepth);
  const offline = !!params.options.offline || !!params.options.offlineDb;
  const results: MultiFolderScanResult[] = [];

  for (const { scanInput, subfolder } of folders) {
    if (scanInput.packages.length === 0) continue;

    if (!params.options.json && !params.options.ratchet) {
      process.stdout.write(`\n${chalk.bold.cyan(`📁 ${subfolder}/`)}\n`);
    }

    const subfolderAbs = path.join(params.projectRoot, subfolder);
    const directDependencyNames = readDirectDependencyNames(subfolderAbs, !!params.options.prodOnly);
    const { findings, completeness } = await scanPackages(scanInput.packages, params.batchSize, params.options, {
      directDependencyNames,
      scanSource: scanInput.source,
      scanFilePath: scanInput.filePath,
    }, undefined, params.fetchImpl);

    // Mirror single-folder scanProject: annotate / filter by source imports per subfolder.
    if (params.options.usage) {
      logInfo(`Scanning ${subfolder}/ source for usage hints...`, params.options);
      const pkgNames = new Set(findings.map(f => f.pkg.name));
      const usageData = scanProjectForPackageUsage(subfolderAbs, pkgNames);
      for (const finding of findings) {
        const files = usageData[finding.pkg.name];
        if (files) {
          finding.usage = {
            imported: files.length > 0,
            files,
          };
        }
      }
    }
    let finalFindings = findings;
    if (params.options.onlyUsed) {
      finalFindings = finalFindings.filter(f => f.usage?.imported);
    }

    let sorted = sortFindingsForOutput(finalFindings);
    let suppressedCount = 0;

    // Non-ratchet: auto-apply an existing per-folder baseline before fix plan,
    // table selection, and maintenance (mirrors single-folder index.ts).
    // --ratchet keeps the full set so handleMultiFolderScan can save or gate.
    if (!params.options.ratchet) {
      const baseline = readBaseline(subfolderAbs);
      if (baseline) {
        const filtered = filterNewFindings(sorted, baseline);
        sorted = filtered.newFindings;
        suppressedCount = filtered.suppressedCount;
      }
    }

    const coverage = buildCoverageNotes(scanInput, offline);
    const minSeverity = normalizeSeverity(params.options.minSeverity || "medium");
    const tableFindings = params.options.all ? sorted : selectFindingsForTable(sorted, minSeverity);
    const suggestedFixCommands = buildSuggestedFixCommandPlan(sorted, scanInput, { offline, subfolder });

    // Override hygiene is independent of the CVE ratchet/baseline. A --ratchet
    // run skips the override audit entirely (same boundary as single-folder).
    let overrideFindings: OverrideFinding[] = [];
    if (params.options.checkOverrides && !params.options.ratchet) {
      const overrideCtx = buildOverrideContext(subfolderAbs, {
        auditLog: params.auditLog ?? NULL_AUDIT_LOG,
        logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
        checkNetwork: !!params.options.checkNetwork,
      });
      const overrideAudit = await audit(overrideCtx, { checkNetwork: !!params.options.checkNetwork });
      overrideFindings = overrideAudit.findings;
    }

    // Maintenance from the baseline-filtered set. Skipped under --ratchet because
    // that path always early-exits on CVE save/gate (same as single-folder).
    let maintenanceFindings: MaintenanceFinding[] = [];
    if (params.options.checkMaintenance && !params.options.ratchet) {
      const directDependencies = scanInput.packages.filter(p => directDependencyNames?.has(p.name));
      maintenanceFindings = await detectDM001(sorted, directDependencies, offline);
    }

    let licenseFindings: LicenseFinding[] = [];
    let licenseLimitedToDirectOnly = false;
    if (params.options.checkLicenses && !params.options.ratchet) {
      const directDeps = scanInput.packages.filter(p => directDependencyNames?.has(p.name));
      const isNpm = scanInput.source === "package-lock" || scanInput.source === "npm-shrinkwrap";
      const licenseResult = await detectLicenseIssues({
        lockfilePath: scanInput.filePath,
        directDeps,
        isNpm,
        isOffline: offline,
      });
      licenseFindings = licenseResult.findings;
      licenseLimitedToDirectOnly = licenseResult.limitedToDirectOnly;
    }

    results.push({
      subfolder,
      scanInput,
      sorted,
      suggestedFixCommands,
      coverage,
      minSeverity,
      tableFindings,
      allPackages: scanInput.packages,
      completeness,
      overrideFindings,
      maintenanceFindings,
      licenseFindings,
      licenseLimitedToDirectOnly,
      suppressedCount,
    });
  }

  return results;
}

/**
 * Per-subfolder --ratchet: each folder gets its own `.cve-lite/baseline.json`.
 * Folders without a baseline are saved; folders with a baseline are gated.
 * Exit 1 if any gated folder has findings above its baseline.
 */
function handleMultiFolderRatchet(
  results: MultiFolderScanResult[],
  projectRoot: string,
  options: ParsedOptions,
): ExitCode {
  let anyNewFindings = false;
  let hasDetectionGaps = false;

  for (const r of results) {
    const { hasDetectionGap } = getCompletenessImpact(r.completeness);
    if (hasDetectionGap) {
      hasDetectionGaps = true;
      console.log(chalk.red(`${r.subfolder}/: Scan data is incomplete. Refusing to create or evaluate a baseline from partial detection data.`));
      for (const diagnostic of r.completeness.diagnostics) {
        if (diagnostic.impact !== "detection") continue;
        console.log(chalk.red(`  ${formatDiagnosticMessage(
          diagnostic.code,
          diagnostic.count,
          diagnostic.affectedPackageCount,
        )}`));
      }
      continue;
    }

    const subfolderAbs = path.join(projectRoot, r.subfolder);
    const baseline = readBaseline(subfolderAbs);
    const outcome = ratchetOutcome(baseline, r.sorted);

    if (outcome.action === "save") {
      writeBaseline(subfolderAbs, r.sorted);
      const count = r.sorted.length;
      console.log(
        chalk.green(
          `✓ ${r.subfolder}/: Baseline saved to .cve-lite/baseline.json with ${count} ${pluralize(count, "finding")}. Future scans will only report findings above this baseline.`,
        ),
      );
      continue;
    }

    const { newFindings, suppressedCount } = outcome;
    const suppressedLabel = `${suppressedCount} existing ${pluralize(suppressedCount, "finding")} suppressed`;
    if (newFindings.length === 0) {
      console.log(chalk.green(`✓ ${r.subfolder}/: No new findings above baseline - ${suppressedLabel}`));
      continue;
    }

    anyNewFindings = true;
    console.log(
      chalk.red(
        `${r.subfolder}/: ${newFindings.length} new ${pluralize(newFindings.length, "finding")} above baseline - ${suppressedLabel}`,
      ),
    );
    for (const f of newFindings) {
      const ids = f.vulnerabilities.map(v => v.id).join(", ");
      console.log(`  ${chalk.yellow(f.severity)} ${f.pkg.name}@${f.pkg.version}${ids ? ` (${ids})` : ""}`);
    }
  }

  if (hasDetectionGaps) {
    return EXIT_ERROR;
  }

  if (options.checkOverrides) {
    console.log(
      chalk.gray(
        `Note: override hygiene (--check-overrides) is not part of the ratchet baseline; run \`${OVERRIDES_COMMAND}\` to audit overrides.`,
      ),
    );
  }

  if (anyNewFindings) {
    console.log(
      chalk.gray(
        "To accept these, re-baseline intentionally by deleting the folder's .cve-lite/baseline.json and re-running --ratchet.",
      ),
    );
    return EXIT_FINDINGS;
  }

  return EXIT_OK;
}

export async function handleMultiFolderScan(params: {
  projectRoot: string;
  batchSize: number;
  options: ParsedOptions;
  fetchImpl?: FetchLike;
  auditLog?: AuditLogHandle;
}): Promise<ExitCode> {
  const auditLog = params.auditLog ?? NULL_AUDIT_LOG;
  const scanStartedAt = Date.now();
  const results = await runMultiFolderScan(params);
  const scanFinishedAt = Date.now();

  const first = results[0];
  auditLog.emit({
    ts: new Date(scanStartedAt).toISOString(),
    type: "scan.started",
    schemaVersion: 1,
    projectPath: params.projectRoot,
    mode: first?.scanInput.mode ?? "resolved-lockfile",
    source: first?.scanInput.source ?? "package-lock",
    flags: {
      fix: params.options.fix === true,
      json: params.options.json === true,
      prodOnly: params.options.prodOnly === true,
      offline: params.options.offline === true,
      checkOverrides: params.options.checkOverrides === true,
      checkMaintenance: params.options.checkMaintenance === true,
      folderCount: String(results.length),
    },
  });

  if (results.length === 0) {
    console.log(chalk.yellow("No scannable packages found in any subfolder."));
    auditLog.emit({
      ts: new Date(scanFinishedAt).toISOString(),
      type: "scan.finished",
      schemaVersion: 1,
      durationMs: scanFinishedAt - scanStartedAt,
      findingsCount: 0,
      exitCode: EXIT_OK,
    });
    return EXIT_OK;
  }

  if (params.options.fix) {
    console.error(chalk.yellow("--fix is not yet supported in multi-folder mode. Run cve-lite . from each subfolder individually."));
    auditLog.emit({
      ts: new Date().toISOString(),
      type: "scan.finished",
      schemaVersion: 1,
      durationMs: Date.now() - scanStartedAt,
      findingsCount: results.reduce((count, result) => count + result.sorted.length, 0),
      exitCode: EXIT_ERROR,
    });
    return EXIT_ERROR;
  }

  if (params.options.sarif || params.options.cdx) {
    console.error(chalk.yellow("--sarif and --cdx are not yet supported in multi-folder mode."));
    auditLog.emit({
      ts: new Date().toISOString(),
      type: "scan.finished",
      schemaVersion: 1,
      durationMs: Date.now() - scanStartedAt,
      findingsCount: results.reduce((count, result) => count + result.sorted.length, 0),
      exitCode: EXIT_ERROR,
    });
    return EXIT_ERROR;
  }

  if (params.options.ratchet) {
    return handleMultiFolderRatchet(results, params.projectRoot, params.options);
  }

  const aggregatedCompleteness = aggregateMultiFolderCompleteness(results);

  if (params.options.json) {
    // Match single-folder writeOutputs: timestamped file in cwd, not stdout dump.
    // Help text and CI both treat --json as "save a JSON file".
    const allFindings = results.flatMap(r =>
      r.sorted.map(f => ({ ...serializeFinding(f, r.suggestedFixCommands), subfolder: r.subfolder })),
    );
    const payload = {
      multiFolder: true as const,
      projectPath: params.projectRoot,
      folders: results.map(r => r.subfolder),
      findingCount: allFindings.length,
      status: aggregatedCompleteness.complete ? "ok" : "partial",
      complete: aggregatedCompleteness.complete,
      diagnostics: aggregatedCompleteness.diagnostics,
      findings: allFindings,
      ...(params.options.checkOverrides
        ? {
            overrideFindings: results.flatMap(r =>
              r.overrideFindings.map(f => ({ ...f, subfolder: r.subfolder })),
            ),
          }
        : {}),
      ...(params.options.checkMaintenance
        ? {
            maintenanceFindings: results.flatMap(r =>
              r.maintenanceFindings.map(f => ({ ...f, subfolder: r.subfolder })),
            ),
          }
        : {}),
      ...(params.options.checkLicenses
        ? {
            licenseFindings: results.flatMap(r =>
              r.licenseFindings.map(f => ({ ...f, subfolder: r.subfolder })),
            ),
          }
        : {}),
      scannedAt: new Date().toISOString(),
    };
    const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const jsonFilename = `cve-lite-scan-${ts}.json`;
    const jsonOutputPath = path.join(resolveOutputDir(params.options.output), jsonFilename);
    fs.writeFileSync(jsonOutputPath, JSON.stringify(payload, null, 2));
    console.log(`${chalk.gray("JSON saved to")} ${chalk.cyan(displayOutputPath(jsonOutputPath))}`);
  } else {
    printMultiFolderResults(results, params.options);
    if (params.options.checkOverrides) {
      const { renderOverrideFindings } = await import("../output/override-findings-terminal.js");
      for (const r of results) {
        process.stdout.write(`\n${chalk.bold.cyan(`📁 ${r.subfolder}/`)} ${chalk.gray("override hygiene")}\n`);
        console.log(renderOverrideFindings(r.overrideFindings, { verbose: !!params.options.verbose, projectPath: path.join(params.projectRoot, r.subfolder) }));
      }
    }
    if (params.options.checkMaintenance) {
      const { renderMaintenanceFindings } = await import("../output/maintenance-terminal.js");
      for (const r of results) {
        process.stdout.write(`\n${chalk.bold.cyan(`📁 ${r.subfolder}/`)} ${chalk.gray("maintenance risk")}\n`);
        console.log(renderMaintenanceFindings(r.maintenanceFindings, { verbose: !!params.options.verbose }));
      }
    }
    if (params.options.checkLicenses) {
      for (const r of results) {
        process.stdout.write(`\n${chalk.bold.cyan(`📁 ${r.subfolder}/`)} ${chalk.gray("license issues")}\n`);
        console.log(renderLicenseFindings(r.licenseFindings, { limitedToDirectOnly: r.licenseLimitedToDirectOnly }));
      }
    }
    if (!params.options.checkOverrides && !params.options.ratchet) {
      for (const r of results) {
        const subfolderPath = path.join(params.projectRoot, r.subfolder);
        if (hasOverrideEntries(subfolderPath)) {
          printOverrideHint();
          break; // one hint is enough even if multiple subfolders have overrides
        }
      }
    }
  }

  if (params.options.report) {
    const outputDir = path.resolve(
      typeof params.options.report === "string" ? params.options.report : "./cve-report"
    );
    const cliVersion = getCliVersion();
    const { reportPath } = await writeMultiFolderHtmlReport({
      outputDir,
      results,
      projectPath: params.projectRoot,
      cliVersion,
      autoOpen: !params.options.noOpen,
      // Same undefined-vs-[] contract as single-folder buildReportData: pass the
      // flag so empty panels render when the check ran with no hits.
      includeOverrides: !!params.options.checkOverrides,
      includeMaintenance: !!params.options.checkMaintenance,
      includeLicenses: !!params.options.checkLicenses,
    });
    console.log(`${chalk.gray("Report:")} ${chalk.cyan(reportPath)}`);
  }

  const failLevel = normalizeSeverity(params.options.failOn);
  const allSorted = results.flatMap(r => r.sorted);
  const allOverrideFindings = results.flatMap(r => r.overrideFindings);
  const allMaintenanceFindings = results.flatMap(r => r.maintenanceFindings);
  // Mirror single-folder exit policy in src/index.ts: CVE + override + maintenance
  // all count toward --fail-on. Without overrides here, multi-folder CI using
  // --check-overrides --fail-on high would exit 0 despite high OA findings.
  const shouldFail =
    allSorted.some(f => severityOrder[f.severity] >= severityOrder[failLevel]) ||
    reachesFailOn(allOverrideFindings, params.options.failOn) ||
    reachesFailOn(allMaintenanceFindings, params.options.failOn);
  const incompleteFailure = shouldFailForIncompleteScan(
    aggregatedCompleteness,
    params.options.incompletePolicy,
  );
  const exitCode = incompleteFailure
    ? EXIT_ERROR
    : shouldFail
      ? EXIT_FINDINGS
      : EXIT_OK;

  auditLog.emit({
    ts: new Date(scanFinishedAt).toISOString(),
    type: "scan.finished",
    schemaVersion: 1,
    durationMs: scanFinishedAt - scanStartedAt,
    findingsCount: allSorted.length,
    exitCode,
  });

  return exitCode;
}
