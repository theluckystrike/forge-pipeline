import path from "node:path";
import process from "node:process";
import { loadPackages, buildNoPackagesMessage } from "../parsers/index.js";
import { scanPackages, buildCoverageNotes, createAdvisorySource } from "../scanner.js";
import { normalizeSeverity } from "../osv/severity.js";
import { OVERRIDES_COMMAND } from "../constants.js";
import { chalk } from "../utils/chalk.js";
import type { DebugLogger } from "../output/debug.js";
import { buildSuggestedFixCommandPlan } from "../remediation/fix-commands.js";
import { scanProjectForPackageUsage } from "../usage/scanner.js";
import { offlineDbSyncHint } from "../utils/network.js";
import { formatAdvisoryDbFreshness } from "../utils/time.js";
import { pluralize } from "../utils/string.js";
import type { FetchLike, ParsedOptions } from "../types.js";
import { EXIT_ERROR } from "../types.js";
import {
  formatAdvisorySourceLine,
  logInfo,
  logWarn,
  printCacheSummary,
  sortFindingsForOutput,
} from "../output/formatters.js";
import { countBySeverity, reachesFailOn } from "../utils/severity.js";
import { buildReportData, writeHtmlReport } from "../output/html-reporter.js";
import { writeOutputs } from "../output/write-outputs.js";
import { selectFindingsForTable } from "../output/finding-display.js";
import {
  printActionSummary,
  printCompactOutput,
  printCoverage,
  printFinalStatus,
  printOverrideHint,
  printSkippedDependencies,
  printSuggestedFixCommands,
  printSuggestedFixCommandSkips,
  printSummary,
  printTable,
} from "../output/printers.js";
import { renderOverrideFindings } from "../output/override-findings-terminal.js";
import { detectDM001 } from "../maintenance/dm001-maintenance-risk.js";
import { renderMaintenanceFindings } from "../output/maintenance-terminal.js";
import type { MaintenanceFinding } from "../maintenance/types.js";
import { detectLicenseIssues } from "../licenses/license-check.js";
import type { LicenseFinding } from "../licenses/types.js";
import { renderLicenseFindings } from "../output/license-terminal.js";
import { readDirectDependencyNames, hasOverrideEntries } from "../utils/package-json.js";
import {
  applyFixesIfRequested,
  type FixExecutionResult,
  printFixModeSummary,
  writeFixResultJson,
  type FixResultJson,
} from "../utils/fix-runner.js";
import type { AuditLogHandle } from "../audit-log/index.js";
import { audit, buildOverrideContext } from "../overrides/index.js";
import type { OverrideFinding } from "../overrides/types.js";
import {
  buildFixResultAppliedEntries,
  createPullRequestForFixes,
} from "../utils/create-pr.js";
import { buildCveFixAppliedEvent } from "../audit-log/events.js";
import { readBaseline, writeBaseline, filterNewFindings, ratchetOutcome } from "../utils/baseline.js";
import { formatDiagnosticMessage, getCompletenessImpact, shouldFailForIncompleteScan } from "./completeness.js";

export interface SingleFolderScanParams {
  projectPath: string;
  projectArg?: string;
  batchSize: number;
  searchDepth: number;
  options: ParsedOptions;
  debugLog: DebugLogger;
  fetchImpl?: FetchLike;
  auditLog: AuditLogHandle;
  scanStartedAt: number;
  cliVersion: string;
}

export async function handleSingleFolderScan(params: SingleFolderScanParams): Promise<number> {
  const {
    projectPath,
    projectArg,
    batchSize,
    searchDepth,
    options,
    debugLog,
    fetchImpl,
    auditLog,
    scanStartedAt,
    cliVersion,
  } = params;

  let advisorySourceLine = "";
  let advisoryDbFreshnessLine: string | null = null;
  let advisoryDbWarning: string | null = null;
  try {
    const advisorySource = createAdvisorySource({
      osvUrl: options.osvUrl,
      offline: options.offline,
      offlineDb: options.offlineDb,
      debugLog,
      fetchImpl,
    });
    advisorySourceLine = advisorySource.sourceLabel;
    debugLog("Advisory source", {
      mode: advisorySource.offline ? "offline" : "online",
      url: options.osvUrl ?? (advisorySource.offline ? null : "https://api.osv.dev"),
      label: advisorySourceLine,
    });
    if (advisorySource.offline) {
      const metadata = advisorySource.advisoryDbMetadata;
      advisoryDbFreshnessLine = formatAdvisoryDbFreshness(metadata?.lastSyncAt ?? null);
      if (advisorySource.advisoryDbIsStale) {
        advisoryDbWarning = metadata?.lastSyncAt
          ? "The local advisory DB appears stale. Re-run `cve-lite advisories sync` to refresh it."
          : "The local advisory DB has no recorded sync timestamp. Re-run `cve-lite advisories sync` to refresh it.";
      }
    }
    advisorySource.cleanup();
  } catch (error) {
    if (options.offline || options.offlineDb) {
      const reason = error instanceof Error ? error.message : String(error);
      throw new Error(`Offline advisory database is not available: ${reason}\n${offlineDbSyncHint(options.offlineDb).join("\n")}`);
    }
    throw error;
  }

  if (!options.json && !options.ratchet) {
    if (options.offline || options.offlineDb) {
      console.log(chalk.gray("Offline mode:") + " " + chalk.yellow("enabled") + " " + chalk.gray("(no external advisory calls will be made)"));
    }
    if (advisorySourceLine) {
      console.log(`${chalk.gray("Advisory source:")} ${formatAdvisorySourceLine(advisorySourceLine)}`);
    }
    if (advisoryDbFreshnessLine) {
      console.log(`${chalk.gray("Advisory DB freshness:")} ${advisoryDbFreshnessLine}`);
    }
  }
  if (advisoryDbWarning) {
    logWarn(advisoryDbWarning, options);
  }

  let scanInput = loadPackages(projectPath, !!options.prodOnly, searchDepth);
  let packages = scanInput.packages;
  if (scanInput.filePath) {
    debugLog("Lockfile selected", {
      source: scanInput.source,
      path: scanInput.filePath,
    });
  }
  debugLog("Packages parsed", {
    count: packages.length,
    source: scanInput.source,
  });

  // Emit scan.started event after loading packages
  const scanStartTime = Date.now();
  auditLog.emit({
    ts: new Date().toISOString(),
    type: "scan.started",
    schemaVersion: 1,
    projectPath,
    mode: scanInput.mode,
    source: scanInput.source,
    flags: {
      fix: options.fix === true,
      json: options.json === true,
      prodOnly: options.prodOnly === true,
      offline: options.offline === true,
      checkOverrides: options.checkOverrides === true,
    },
  });

  if (!options.ratchet) {
    logInfo(
      `Parsed ${packages.length} ${pluralize(packages.length, "package")} from ${scanInput.source}${
        scanInput.filePath ? ` (${path.relative(projectPath, scanInput.filePath) || path.basename(scanInput.filePath)})` : ""
      }`,
      options
    );
    printCacheSummary(options.cacheDir, options);
  }

  if (scanInput.warnings.length > 0) {
    for (const warning of scanInput.warnings) {
      logWarn(warning, options);
    }
  }

  if (packages.length === 0) {
    debugLog("Scan skipped", { reason: "no packages found", projectPath });
    logWarn(buildNoPackagesMessage(projectPath), options);
    auditLog.emit({
      ts: new Date().toISOString(),
      type: "scan.finished",
      schemaVersion: 1,
      durationMs: Date.now() - scanStartTime,
      findingsCount: 0,
      exitCode: 0,
    });
    return 0;
  }

  if (!options.json && !options.ratchet) console.log();
  let scanState = await scanProject({
    scanInput,
    batchSize,
    options,
    projectPath,
    debugLog,
    fetchImpl,
  });
  const findingsBeforeFixList = scanState.sorted;
  const findingsBeforeFix = findingsBeforeFixList.length;
  let fixResult: FixExecutionResult | null = null;
  let baseline = readBaseline(projectArg ?? ".");
  let suppressedCount = 0;

  // Collect override findings if --check-overrides is set.
  // Boundary: override hygiene is independent of the CVE ratchet/baseline. The
  // baseline only ever records CVE findings (see src/utils/baseline.ts), so a
  // --ratchet run skips the override audit entirely - override findings are never
  // baselined or suppressed.
  let overrideFindings: OverrideFinding[] = [];
  if (options.checkOverrides && !options.ratchet) {
    const overrideCtx = buildOverrideContext(projectPath, {
      auditLog,
      logger: {
        info: (msg: string) => debugLog("oa.info", { message: msg }),
        warn: (msg: string) => debugLog("oa.warn", { message: msg }),
        error: (msg: string) => debugLog("oa.error", { message: msg }),
        debug: (msg: string) => debugLog("oa.debug", { message: msg }),
      },
      checkNetwork: !!options.checkNetwork,
    });
    const auditResult = await audit(overrideCtx, { checkNetwork: !!options.checkNetwork });
    overrideFindings = auditResult.findings;
  }

  let maintenanceFindings: MaintenanceFinding[] = [];
  let licenseFindings: LicenseFinding[] = [];
  let licenseLimitedToDirectOnly = false;

  // Emit cve.detected for each CVE finding
  for (const f of scanState.sorted) {
    auditLog.emit({
      ts: new Date().toISOString(),
      type: "cve.detected",
      schemaVersion: 1,
      package: { name: f.pkg.name, version: f.pkg.version },
      severity: f.severity,
      cveAliases: f.cveAliases,
      vulnerabilityIds: f.vulnerabilities.map((v) => v.id),
    });
  }

  if (options.fix) {
    fixResult = await applyFixesIfRequested({
      plan: scanState.suggestedFixCommands,
      projectPath,
      totalFindings: scanState.sorted.length,
      options,
      debugLog,
    });

    if (fixResult.appliedFixCount > 0) {
      console.log(`${chalk.cyan("⠋")} ${chalk.gray("Rescanning project...")}`);
      scanInput = loadPackages(projectPath, !!options.prodOnly, searchDepth);
      packages = scanInput.packages;
      if (packages.length === 0) {
        debugLog("Scan skipped", { reason: "no packages found after fix rescan", projectPath });
        logWarn(buildNoPackagesMessage(projectPath), options);
        auditLog.emit({
          ts: new Date().toISOString(),
          type: "scan.finished",
          schemaVersion: 1,
          durationMs: Date.now() - scanStartTime,
          findingsCount: 0,
          exitCode: 0,
        });
        return 0;
      }

      scanState = await scanProject({
        scanInput,
        batchSize,
        options,
        projectPath,
        debugLog,
        fetchImpl,
      });
    }
  }

  let overridesFixHookResult = null;
  // Override hygiene is opt-in. Only run the fix hook (which can patch
  // package.json) when --check-overrides was requested, so `cve-lite . --fix`
  // stays a pure CVE operation and never touches overrides unasked.
  if (options.fix && fixResult && options.checkOverrides) {
    const { runOverridesFixHook } = await import("../cli/fix-overrides-hook.js");
    const projectPathResolved = path.resolve(projectArg ?? ".");

    // Collect CVE-touched targets from cve-lite's fix result.
    const cveFixTargets = fixResult.applied.map((entry) => ({
      name: entry.package,
      version: entry.to,
    }));

    // Create a simple logger adapter if needed
    const hookLogger = {
      info: (msg: string) => debugLog("hook.info", { message: msg }),
      warn: (msg: string) => debugLog("hook.warn", { message: msg }),
      error: (msg: string) => debugLog("hook.error", { message: msg }),
      debug: (msg: string) => debugLog("hook.debug", { message: msg }),
    };

    overridesFixHookResult = await runOverridesFixHook({
      projectPath: projectPathResolved,
      auditLog,
      logger: hookLogger,
      cveFixTargets,
    });

    if (!overridesFixHookResult.verifyOk) {
      debugLog("overrides-fix-hook verify failed", {
        failures: overridesFixHookResult.verifyFailures,
      });
      console.log(
        chalk.red(
          `Overrides fix verify failed:\n${overridesFixHookResult.verifyFailures
            .map((v) => `  ${v.ruleId} ${v.package}: ${v.reason}`)
            .join("\n")}`
        )
      );
      auditLog.emit({
        ts: new Date().toISOString(),
        type: "scan.finished",
        schemaVersion: 1,
        durationMs: Date.now() - scanStartTime,
        findingsCount: scanState.sorted.length + overrideFindings.length,
        exitCode: 2,
      });
      return 2;
    }
  }

  // Emit cve.fix.applied for each target in the fix plan
  if (scanState.suggestedFixCommands?.targets) {
    for (const target of scanState.suggestedFixCommands.targets) {
      auditLog.emit(buildCveFixAppliedEvent({
        ts: new Date().toISOString(),
        package: target.package,
        fromVersion: target.currentVersion ?? "unknown",
        toVersion: target.targetVersion,
        mechanism: target.kind,
        childPackage: target.childPackage,
        childTargetVersion: target.childTargetVersion,
      }));
    }
  }

  if (options.fix) {
    printFixModeSummary({
      fixResult,
      findingsBeforeFix,
      findingsAfterFix: scanState.sorted.length,
      remainingBySeverity: countBySeverity(scanState.sorted),
    });

    // Write fix result JSON for Action-level PR creation.
    // Written even when appliedFixCount is 0 so the Action can detect
    // the nothing-to-fix case without parsing stdout.
    const fixResultJson: FixResultJson = {
      appliedFixCount: fixResult?.appliedFixCount ?? 0,
      appliedWithinRangeRefreshCount: fixResult?.appliedWithinRangeRefreshCount ?? 0,
      findingsBeforeFix,
      findingsAfterFix: scanState.sorted.length,
      applied: buildFixResultAppliedEntries(fixResult?.applied ?? [], findingsBeforeFixList),
      notAutoApplied: {
        parentUpgradeCount: fixResult?.parentUpgradeCount ?? 0,
        breakingUpgradeCount: fixResult?.breakingUpgradeCount ?? 0,
        noFixCount: fixResult?.noFixCount ?? 0,
      },
    };
    writeFixResultJson(fixResultJson, projectPath);

    if (options.createPr && fixResult) {
      // Override hygiene fixes also land in package.json (staged by create-pr), so
      // a PR is warranted when either CVE fixes or override fixes were applied.
      const overrideFixCount = overridesFixHookResult?.applied ?? 0;
      if (fixResult.appliedFixCount === 0 && overrideFixCount === 0) {
        logWarn("Skipping pull request creation: no direct fixes were applied.", options);
      } else {
        console.log("");
        console.log(chalk.bold.cyan("Creating pull request (--create-pr)"));
        const prResult = await createPullRequestForFixes({
          projectPath,
          baseBranch: options.prBase ?? "main",
          fixResult,
          findingsBeforeFix: findingsBeforeFixList,
          findingsAfterFix: scanState.sorted,
          overrideFixCount,
        });
        if (prResult.skipped) {
          logWarn(prResult.skipReason ?? "Pull request was not created.", options);
        } else if (prResult.prUrl) {
          console.log(`${chalk.gray("Pull request:")} ${chalk.cyan(prResult.prUrl)}`);
          console.log(`${chalk.gray("Branch:")} ${chalk.cyan(prResult.branchName)}`);
        } else {
          logWarn(`Branch ${prResult.branchName} was pushed, but no pull request URL was returned.`, options);
        }
      }
    }
  } else {
    // --ratchet: with no baseline yet, save the current findings. With an
    // existing baseline, GATE instead of re-saving - fail on findings not in the
    // baseline. Re-saving here would silently absorb a new vulnerability into a
    // fresh baseline, so a ratcheted CI job could never fail on a regression.
    if (options.ratchet) {
      const { hasDetectionGap } = getCompletenessImpact(scanState.completeness);
      if (hasDetectionGap) {
        console.log(chalk.red("Scan data is incomplete. Refusing to create or evaluate a baseline from partial detection data."));
        for (const diagnostic of scanState.completeness.diagnostics) {
          if (diagnostic.impact !== "detection") continue;
          console.log(chalk.red(`  ${formatDiagnosticMessage(
            diagnostic.code,
            diagnostic.count,
            diagnostic.affectedPackageCount,
          )}`));
        }
        auditLog.emit({
          ts: new Date().toISOString(),
          type: "scan.finished",
          schemaVersion: 1,
          durationMs: Date.now() - scanStartTime,
          findingsCount: scanState.sorted.length,
          exitCode: EXIT_ERROR,
        });
        return EXIT_ERROR;
      }
      const outcome = ratchetOutcome(baseline, scanState.sorted);
      if (outcome.action === "save") {
        writeBaseline(projectArg ?? ".", scanState.sorted);
        const count = scanState.sorted.length;
        console.log(chalk.green(`✓ Baseline saved to .cve-lite/baseline.json with ${count} ${count === 1 ? "finding" : "findings"}. Future scans will only report findings above this baseline.`));
        if (options.checkOverrides) {
          console.log(chalk.gray(`Note: override hygiene (--check-overrides) is not part of the ratchet baseline; run \`${OVERRIDES_COMMAND}\` to audit overrides.`));
        }
        auditLog.emit({
          ts: new Date().toISOString(),
          type: "scan.finished",
          schemaVersion: 1,
          durationMs: Date.now() - scanStartTime,
          findingsCount: scanState.sorted.length,
          exitCode: 0,
        });
        return 0;
      }

      const { newFindings, suppressedCount: sc } = outcome;
      const suppressedLabel = `${sc} existing ${sc === 1 ? "finding" : "findings"} suppressed`;
      if (newFindings.length === 0) {
        console.log(chalk.green(`No new findings above baseline - ${suppressedLabel}`));
        auditLog.emit({
          ts: new Date().toISOString(),
          type: "scan.finished",
          schemaVersion: 1,
          durationMs: Date.now() - scanStartTime,
          findingsCount: scanState.sorted.length,
          exitCode: 0,
        });
        return 0;
      }
      console.log(chalk.red(`${newFindings.length} new ${newFindings.length === 1 ? "finding" : "findings"} above baseline - ${suppressedLabel}`));
      for (const f of newFindings) {
        const ids = f.vulnerabilities.map(v => v.id).join(", ");
        console.log(`  ${chalk.yellow(f.severity)} ${f.pkg.name}@${f.pkg.version}${ids ? ` (${ids})` : ""}`);
      }
      console.log(chalk.gray("To accept these, re-baseline intentionally by deleting .cve-lite/baseline.json and re-running --ratchet."));
      auditLog.emit({
        ts: new Date().toISOString(),
        type: "scan.finished",
        schemaVersion: 1,
        durationMs: Date.now() - scanStartTime,
        findingsCount: newFindings.length,
        exitCode: 1,
      });
      return 1;
    }

    // auto-apply baseline if it exists - filter before output
    if (baseline) {
      const filtered = filterNewFindings(scanState.sorted, baseline);
      scanState.sorted = filtered.newFindings;
      scanState.tableFindings = scanState.tableFindings.filter(f =>
        filtered.newFindings.some(nf => nf.pkg.name === f.pkg.name && nf.pkg.version === f.pkg.version)
      );
      suppressedCount = filtered.suppressedCount;
    }

    // Maintenance risk findings are derived from CVE findings (via
    // recommendedParentUpgrade), so they must be computed from the same
    // baseline-filtered set everything below uses (JSON, rendering,
    // --fail-on). Computing this earlier - before the baseline filter above -
    // let a DM001 finding on an already-baselined CVE keep failing
    // --fail-on forever, even as printFinalStatus reported a clean scan.
    // This point is unreached in --ratchet mode (which always returns above),
    // so packument fetches never run wastefully there.
    if (options.checkMaintenance) {
      const directNames = readDirectDependencyNames(projectPath, !!options.prodOnly);
      const directDependencies = scanState.allPackages.filter(p => directNames?.has(p.name));
      maintenanceFindings = await detectDM001(
        scanState.sorted,
        directDependencies,
        !!options.offline || !!options.offlineDb,
      );
    }

    if (options.checkLicenses) {
      const directNames = readDirectDependencyNames(projectPath, !!options.prodOnly);
      const directDeps = scanState.allPackages.filter(p => directNames?.has(p.name));
      const licenseResult = await detectLicenseIssues({
        lockfilePath: scanInput.filePath,
        directDeps,
        isNpm: scanInput.source === "package-lock" || scanInput.source === "npm-shrinkwrap",
        isOffline: !!options.offline || !!options.offlineDb,
      });
      licenseFindings = licenseResult.findings;
      licenseLimitedToDirectOnly = licenseResult.limitedToDirectOnly;
    }

    await writeOutputs(options, {
      sorted: scanState.sorted,
      allPackages: scanState.allPackages,
      suggestedFixCommands: scanState.suggestedFixCommands,
      coverage: scanState.coverage,
      minSeverity: scanState.minSeverity,
      tableFindings: scanState.tableFindings,
      completeness: scanState.completeness,
      overrideFindings,
      maintenanceFindings,
      licenseFindings,
      licenseLimitedToDirectOnly,
    }, scanInput, projectPath);

    if (!(options.json || options.sarif || options.sbom) || options.verbose) {
      const offline = !!options.offline || !!options.offlineDb;
      const showOverrideHint = !options.checkOverrides && !options.ratchet && hasOverrideEntries(projectPath);
      if (options.verbose) {
        const overrideCount = options.checkOverrides ? overrideFindings.length : 0;
        printSummary(scanState.sorted, packages.length, scanInput);
        const pmLabel = scanState.suggestedFixCommands
          ? `${chalk.cyan(scanState.suggestedFixCommands.packageManager)} ${chalk.gray(`(${scanState.suggestedFixCommands.sourceLabel})`)}`
          : undefined;
        printActionSummary(scanState.sorted, overrideCount, pmLabel);
        printSuggestedFixCommands(scanState.sorted, scanInput, { offline, overrideCount });
        printSuggestedFixCommandSkips(scanState.sorted, scanInput, { offline });
        if (scanInput.skippedDependencies.length > 0) {
          printSkippedDependencies(scanInput.skippedDependencies);
        }
        if (scanState.sorted.length > 0) {
          if (scanState.tableFindings.length > 0) {
            const skippedKeys = new Set(
              (scanState.suggestedFixCommands?.skipped ?? []).map(s => `${s.package}@${s.version}`)
            );
            printTable(scanState.tableFindings, options.all ? null : scanState.minSeverity, skippedKeys, scanState.suggestedFixCommands);
          } else {
            logInfo(`No findings met the table threshold of ${scanState.minSeverity}. Re-run with --all to show everything.`, options);
          }
        }
        if (options.checkOverrides && overrideFindings.length > 0) {
          console.log("\n" + renderOverrideFindings(overrideFindings, { verbose: true, projectPath }));
        }
        if (options.checkMaintenance && maintenanceFindings.length > 0) {
          console.log("\n" + renderMaintenanceFindings(maintenanceFindings, { verbose: true }));
        }
        if (options.checkLicenses) {
          console.log("\n" + renderLicenseFindings(licenseFindings, { limitedToDirectOnly: licenseLimitedToDirectOnly }));
        }
        printCoverage([...scanInput.notes, ...scanState.coverage]);
        printFinalStatus(scanState.sorted, overrideCount, scanState.completeness);
        if (showOverrideHint) printOverrideHint();
      } else {
        const compactPmLabel = scanState.suggestedFixCommands
          ? `${chalk.cyan(scanState.suggestedFixCommands.packageManager)} ${chalk.gray(`(${scanState.suggestedFixCommands.sourceLabel})`)}`
          : undefined;
        printCompactOutput(scanState.sorted, scanInput, {
          offline,
          all: !!options.all,
          packageManager: compactPmLabel,
          completeness: scanState.completeness,
          licenseFindings: options.checkLicenses ? licenseFindings : undefined,
          licenseLimitedToDirectOnly: options.checkLicenses ? licenseLimitedToDirectOnly : undefined,
        });
        if (options.checkOverrides) {
          console.log("\n" + renderOverrideFindings(overrideFindings, { verbose: false, projectPath }));
        }
        if (options.checkMaintenance && maintenanceFindings.length > 0) {
          console.log("\n" + renderMaintenanceFindings(maintenanceFindings, { verbose: false }));
        }
        if (showOverrideHint) printOverrideHint();
      }
    }
  }

  if (options.report) {
    const outputDir = path.resolve(
      typeof options.report === "string" ? options.report : "./cve-report"
    );
    const reportData = buildReportData({
      projectPath,
      cliVersion,
      packageManager: scanInput.source,
      lockfileSource: scanInput.filePath ? path.basename(scanInput.filePath) : scanInput.source,
      packageCount: packages.length,
      findings: scanState.sorted,
      suggestedFixCommands: scanState.suggestedFixCommands,
      notes: [...scanInput.notes, ...scanState.coverage],
      warnings: scanInput.warnings,
      skippedDependencies: scanInput.skippedDependencies,
      // undefined (not []) when override checking was not requested, so the HTML
      // report omits the Override hygiene panel entirely on a plain scan.
      overrideFindings: options.checkOverrides ? overrideFindings : undefined,
      // Same undefined-vs-[] convention as overrideFindings above.
      maintenanceFindings: options.checkMaintenance ? maintenanceFindings : undefined,
      licenseFindings: options.checkLicenses ? licenseFindings : undefined,
      licenseLimitedToDirectOnly: options.checkLicenses ? licenseLimitedToDirectOnly : undefined,
      completeness: scanState.completeness,
    });
    const { reportPath } = await writeHtmlReport({
      outputDir,
      data: reportData,
      autoOpen: !options.noOpen,
    });
    console.log(`${chalk.gray("Report:")} ${chalk.cyan(reportPath)}`);
  }

  debugLog("Scan finished", {
    totalDurationMs: Date.now() - scanStartedAt,
    findings: scanState.sorted.length,
    packages: packages.length,
  });

  if (baseline) {
    if (scanState.sorted.length === 0) {
      console.log(chalk.green(`No new findings above baseline - ${suppressedCount} existing ${suppressedCount === 1 ? "finding" : "findings"} suppressed`));
    } else {
      console.log(chalk.yellow(`${scanState.sorted.length} new ${scanState.sorted.length === 1 ? "finding" : "findings"} above baseline - ${suppressedCount} existing ${suppressedCount === 1 ? "finding" : "findings"} suppressed`));
    }
  }

  // Override hygiene findings count toward --fail-on too, using the shared
  // reachesFailOn helper from src/utils/severity.ts, the same logic used by
  // the standalone `overrides` command. Without this, a CI run
  // of `cve-lite . --check-overrides --fail-on high` would exit 0 despite high-severity
  // override findings, giving a false sense of protection. overrideFindings is empty
  // unless --check-overrides (and non-ratchet), so this is a no-op otherwise.
  const shouldFail =
    reachesFailOn(scanState.sorted, options.failOn) ||
    reachesFailOn(overrideFindings, options.failOn) ||
    reachesFailOn(maintenanceFindings, options.failOn);
  // In fix mode, remaining transitive findings cannot be auto-fixed.
  // Exiting non-zero would prevent the Action PR step from running.
  const incompleteFailure = shouldFailForIncompleteScan(
    scanState.completeness,
    options.incompletePolicy,
  );
  const exitCode = incompleteFailure
    ? EXIT_ERROR
    : shouldFail && !options.fix
      ? 1
      : 0;

  // Emit scan.finished event and return exitCode
  auditLog.emit({
    ts: new Date().toISOString(),
    type: "scan.finished",
    schemaVersion: 1,
    durationMs: Date.now() - scanStartTime,
    findingsCount: scanState.sorted.length + overrideFindings.length,
    exitCode,
  });

  return exitCode;
}

export async function scanProject(params: {
  scanInput: ReturnType<typeof loadPackages>;
  batchSize: number;
  options: ParsedOptions;
  projectPath: string;
  debugLog: DebugLogger;
  fetchImpl?: FetchLike;
}) {
  const directDependencyNames = readDirectDependencyNames(params.projectPath, !!params.options.prodOnly);
  const { findings, completeness } = await scanPackages(params.scanInput.packages, params.batchSize, params.options, {
    directDependencyNames,
    scanSource: params.scanInput.source,
    scanFilePath: params.scanInput.filePath,
  }, params.debugLog, params.fetchImpl);

  if (params.options.usage) {
    logInfo(`Scanning project source for usage hints...`, params.options);
    const usageStartedAt = Date.now();
    const pkgNames = new Set(findings.map(f => f.pkg.name));
    const usageData = scanProjectForPackageUsage(params.projectPath, pkgNames);
    let matchedPackages = 0;
    for (const finding of findings) {
      const files = usageData[finding.pkg.name];
      if (files) {
        if (files.length > 0) {
          matchedPackages += 1;
        }
        finding.usage = {
          imported: files.length > 0,
          files,
        };
      }
    }
    if (params.options.debug) {
      params.debugLog("Usage scan", {
        durationMs: Date.now() - usageStartedAt,
        packagesChecked: pkgNames.size,
        matchedPackages,
      });
    }
  }
  let finalFindings = findings;
  if (params.options.onlyUsed) {
    const beforeCount = finalFindings.length;
    finalFindings = finalFindings.filter(f => f.usage?.imported);
    if (params.options.debug) {
      params.debugLog("Findings filtered", {
        reason: "only-used",
        before: beforeCount,
        after: finalFindings.length,
      });
    }
  }

  const offline = !!params.options.offline || !!params.options.offlineDb;
  const sorted = sortFindingsForOutput(finalFindings);
  const coverage = buildCoverageNotes(params.scanInput, offline);
  const minSeverity = normalizeSeverity(params.options.minSeverity || "medium");
  const tableFindings = params.options.all
    ? sorted
    : selectFindingsForTable(sorted, minSeverity);
  const suggestedFixCommands = buildSuggestedFixCommandPlan(sorted, params.scanInput, { offline });

  return {
    sorted,
    coverage,
    minSeverity,
    tableFindings,
    suggestedFixCommands,
    allPackages: params.scanInput.packages,
    completeness,
  };
}
