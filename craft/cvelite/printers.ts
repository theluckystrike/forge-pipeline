import type { Finding, ScanCompleteness, ScanInput, SeverityLabel } from "../types.js";
import type { LicenseFinding } from "../licenses/types.js";
import { chalk, stripAnsi } from "../utils/chalk.js";
import { buildSuggestedFixCommandPlan, planVersionForFinding, UNVERIFIED_PARENT_UPGRADE_NOTE, type SuggestedFixTarget, type SuggestedFixCommandPlan } from "../remediation/fix-commands.js";
import { formatParentUpdateChildNote } from "../remediation/parent-update-child-note.js";
import { isBreakingUpgrade } from "../utils/version.js";
import { getPrimaryParent } from "../utils/finding.js";
import {
  countUniqueAdvisories,
  countProdFindings,
  formatRelationshipLabel,
  formatRelLabel,
  formatRootDependencySummary,
  sortFindingsForOutput,
  formatFixCommandWithPublishDates,
  formatCooldownWarning,
} from "./formatters.js";
import { formatSeverityLabel } from "../utils/severity.js";
import { severityOrder } from "../constants.js";
import { pluralize } from "../utils/string.js";
import { hasMaliciousAdvisory } from "../utils/vuln.js";
import { selectFindingsForCompact } from "./finding-display.js";
import {
  COMPACT_COMMAND_GROUP_LIMIT,
  COMPACT_FINDING_BLOCK_LIMIT,
  formatCompactCommandGroupTruncationNotice,
  formatCompactFindingTruncationNotice,
} from "./compact-truncation.js";
import { computePrioritySignal, PRIORITY_SIGNAL_LABELS, PRIORITY_SIGNAL_TABLE_LABELS, PRIORITY_SIGNAL_DESCRIPTIONS, type PrioritySignal } from "../utils/priority-signal.js";
import { computeContextualSignals, formatContextualSignalValues, formatContextualSignalsLine } from "../utils/contextual-signals.js";
import { renderLicenseFindings } from "./license-terminal.js";
import { getCompletenessImpact } from "../scan/completeness.js";
import {
  MAL_PRIVATE_REGISTRY_COMPACT_MESSAGE,
  MAL_PRIVATE_REGISTRY_LEGEND_MESSAGE,
  MAL_GIT_SOURCE_PINNED_MESSAGE,
  MAL_GIT_SOURCE_FLOATING_MESSAGE,
  MAL_GIT_SOURCE_COMPACT_MESSAGE,
  MAL_GIT_SOURCE_LEGEND_MESSAGE,
  MAL_GIT_SOURCE_PINNED_DISPLAY,
  MAL_GIT_SOURCE_FLOATING_DISPLAY,
  OVERRIDES_COMMAND,
} from "../constants.js";

export function printSummary(findings: Finding[], packageCount: number, scanInput: ScanInput) {
  if (findings.length === 0) {
    if (scanInput.mode === "manifest-fallback") {
      console.log(chalk.greenBright(`✓ No known OSV matches found for manifest fallback packages (${packageCount} exact direct dependencies checked)`));
    } else {
      console.log(chalk.greenBright(`✓ No known OSV vulnerability matches found in parsed lockfile packages (${packageCount} checked)`));
    }
    return;
  }

  const totalCVEs = countUniqueAdvisories(findings);
  const uniquePkgCount = new Set(findings.map(f => `${f.pkg.name}@${f.pkg.version}`)).size;
  const pkgLabel = uniquePkgCount === 1 ? "package" : "packages";
  const cveLabel = totalCVEs === 1 ? "CVE" : "CVEs";

  const counts = {
    critical: findings.filter(f => f.severity === "critical").length,
    high: findings.filter(f => f.severity === "high").length,
    medium: findings.filter(f => f.severity === "medium").length,
    low: findings.filter(f => f.severity === "low").length,
    unknown: findings.filter(f => f.severity === "unknown").length
  };

  console.log(chalk.redBright(`✗ Found ${uniquePkgCount} ${pkgLabel} (${totalCVEs} ${cveLabel}) with known OSV matches from ${scanInput.source}`));
  console.log(renderSeverityTable(counts));
  const prodSplit = countProdFindings(findings);
  if (prodSplit !== null) {
    console.log(chalk.gray(`  └ ${prodSplit.prodTotal} of ${prodSplit.total} findings in prod dependencies`));
  }
}

export function printActionSummary(findings: Finding[], overrideCount = 0, packageManager?: string) {
  if (findings.length === 0 && overrideCount === 0) return;
  const direct = findings.filter(f => f.relationship === "direct").length;
  const transitive = findings.filter(f => f.relationship === "transitive").length;
  const unknown = findings.filter(f => f.relationship === "unknown").length;
  const uniqueAdvisories = countUniqueAdvisories(findings);
  const fixable = findings.filter(f => Boolean(f.firstFixedVersion)).length;

  console.log("");
  console.log(chalk.bold.cyan("Quick take"));
  if (packageManager) {
    console.log(`- ${chalk.gray("Package manager:")} ${packageManager}`);
  }
  if (findings.length > 0) {
    console.log(`- ${chalk.green(String(direct))} vulnerable ${pluralize(direct, "package")} ${direct === 1 ? "looks" : "look"} directly fixable in this project.`);
    console.log(`- ${chalk.yellow(String(transitive))} ${pluralize(transitive, "issue")} ${transitive === 1 ? "comes" : "come"} through other dependencies.`);
    if (unknown > 0) {
      console.log(`- ${chalk.magenta(String(unknown))} ${pluralize(unknown, "package")} could not be clearly classified as direct or transitive.`);
    }
    console.log(`- ${chalk.blueBright(String(uniqueAdvisories))} ${pluralize(uniqueAdvisories, "CVE")} matched overall.`);
    console.log(`- ${chalk.blue(String(fixable))} ${pluralize(fixable, "package")} include a fixed-version hint from OSV.`);
  }
  if (overrideCount > 0) {
    console.log(`- ${chalk.yellow(String(overrideCount))} override hygiene ${pluralize(overrideCount, "issue")} found. Run ${chalk.white(`${OVERRIDES_COMMAND} --fix`)} to address ${pluralize(overrideCount, "it", "them")}.`);
  }
}

function printCooldownWarning(target: SuggestedFixTarget): void {
  if (target.cooldownWarning) {
    console.log(chalk.yellow(`  ⚠ ${formatCooldownWarning(target.cooldownWarning)}`));
  }
}

function printUnverifiedParentUpgradeWarning(target: SuggestedFixTarget): void {
  if (target.confidence === "unverified") {
    console.log(chalk.yellow(`  ${UNVERIFIED_PARENT_UPGRADE_NOTE}`));
  }
}


export function printSuggestedFixCommands(
  findings: Finding[],
  scanInput: ScanInput,
  options?: { offline?: boolean; subfolder?: string; overrideCount?: number },
) {
  const plan = buildSuggestedFixCommandPlan(findings, scanInput, options);
  if (!plan) return;
  const fixRowContexts = buildFixRowContexts(findings);
  if (plan.sections.length === 0) return;
  // One decision for every fix table in the run, so sections that share widths
  // cannot disagree about whether the Usage column exists.
  const showUsage = findings.some(finding => !!finding.usage);
  const sharedActionTableWidths = computeSharedActionTableWidths(plan.sections, showUsage, fixRowContexts);

  console.log("");
  console.log(chalk.bold.yellow("🛠  Suggested Fix Commands"));
  console.log(chalk.white(formatFixCommandSummary(plan)));

  for (const section of plan.sections) {
    console.log("");
    console.log(colorFixSectionTitle(section.severity, section.title));

    // One table per section, always, holding every target the section covers.
    // Direct and parent upgrades used to go in separately shaped tables chosen by
    // section kind, which is why the same title drew a 7-column table in one
    // project and a 4-column one in another, and why a section whose targets
    // matched neither shape drew no table at all.
    const remainingNotes: string[] = [];
    printActionTargetsTable(
      section.targets,
      remainingNotes,
      sharedActionTableWidths,
      fixRowContexts,
      showUsage,
    );
    for (const note of remainingNotes) {
      console.log(chalk.gray(`  Note: ${note}`));
    }

    for (const target of section.targets) {
      printCooldownWarning(target);
      printUnverifiedParentUpgradeWarning(target);
    }
    console.log(renderCommandCallout(section.command, section.targets));
  }

  if (plan.coveredFindingCount > 0) {
    console.log("");
    const coverage = plan.coveredFindingCount === plan.totalFindingCount
      ? chalk.gray(`Running all commands above should fix all ${plan.totalFindingCount} vulnerability ${pluralize(plan.totalFindingCount, "finding")}.`)
      : chalk.gray(`Running all commands above should fix ${chalk.white(String(plan.coveredFindingCount))} of ${chalk.white(String(plan.totalFindingCount))} vulnerability findings.`);
    console.log(coverage);
    const overrideCount = options?.overrideCount ?? 0;
    if (overrideCount > 0) {
      console.log(chalk.gray(`${overrideCount} override hygiene ${pluralize(overrideCount, "issue")} also ${pluralize(overrideCount, "requires", "require")} attention - see the Override Hygiene section below.`));
    }
  }
}

export function printSuggestedFixCommandSkips(
  findings: Finding[],
  scanInput: ScanInput,
  options?: { offline?: boolean; subfolder?: string },
) {
  const plan = buildSuggestedFixCommandPlan(findings, scanInput, options);
  if (!plan || plan.skipped.length === 0) return;

  const unpublishable = plan.skipped.filter(skipped => skipped.reason.includes("not published on npm"));
  // Only surface direct-dependency skips here. Transitive findings without an
  // auto-fix path are already covered by the fix plan step 2 ("Review these urgent
  // transitive issues"), so repeating them here creates confusing duplication.
  const remaining = plan.skipped.filter(skipped =>
    !skipped.reason.includes("not published on npm") && skipped.relationship === "direct"
  );

  if (unpublishable.length > 0) {
    console.log("");
    console.log(chalk.gray("Unpublishable fixed-version hints:"));
    for (const skipped of unpublishable.slice(0, 5)) {
      console.log(`- ${skipped.package}@${skipped.version}: ${skipped.reason}`);
    }
    if (unpublishable.length > 5) {
      console.log(`- ...and ${unpublishable.length - 5} more`);
    }
  }

  if (remaining.length > 0) {
    console.log("");
    console.log(chalk.gray("No auto-fix command available for these direct dependencies:"));
    for (const skipped of remaining.slice(0, 5)) {
      console.log(`- ${skipped.package}@${skipped.version}: ${skipped.reason}`);
    }
    if (remaining.length > 5) {
      console.log(`- ...and ${remaining.length - 5} more`);
    }
  }
}

export function printCoverage(notes: string[]) {
  if (notes.length === 0) return;
  console.log("");
  console.log(chalk.bold.blue("Coverage notes"));
  for (const note of notes) {
    console.log(`${chalk.blue("•")} ${note}`);
  }
}

export function printSkippedDependencies(skipped: string[]) {
  console.log("");
  console.log(chalk.bold.yellow("Skipped manifest dependencies"));
  for (const item of skipped.slice(0, 10)) {
    console.log(`${chalk.yellow("•")} ${item}`);
  }
  if (skipped.length > 10) {
    console.log(`${chalk.yellow("•")} ...and ${skipped.length - 10} more`);
  }
}

function formatPrioritySignal(signal: PrioritySignal | null): string {
  if (!signal) return chalk.gray("-");
  const label = PRIORITY_SIGNAL_TABLE_LABELS[signal];
  if (signal === "fix_now") return chalk.red(label);
  if (signal === "fix_soon") return chalk.yellow(label);
  if (signal === "monitor") return chalk.blue(label);
  return chalk.gray(label);
}

// The single source of truth for every terminal table.
//
// Tables differ in WHICH columns they show, never in what a column is called,
// where it sits, or how its value is rendered. Selection goes through
// `selectColumns`, which filters this array and therefore always returns
// registry order, so two tables cannot disagree about ordering even if their
// name lists are written in a different sequence.
type TableColumn = {
  name: string;
  header: string;
  cap?: number;
  /** Per-column width ceiling for wrapped tables; falls back to `cap`. */
  wrapCap?: number;
  cell: (row: TableRow) => { value: string; decorated?: string };
};

/**
 * The shape every table row is adapted into before rendering.
 *
 * Findings and fix-plan targets are different types with different fields, so
 * each gets an adapter rather than each table re-deriving cells by hand. A cell
 * renders "-" for anything absent, which is what lets a table select a column
 * its rows do not populate without special-casing.
 */
type TableRow = {
  package: string;
  packageDecorated?: string;
  version: string;
  severity?: SeverityLabel | null;
  relationship?: string | null;
  root?: string | null;
  usage?: { imported: boolean; files: string[] } | null;
  advisoryVersion?: string | null;
  target?: string | null;
  scanned?: number | null;
  stillVulnerable?: number | null;
  breaking?: boolean;
  epss?: number | null;
  signal?: PrioritySignal | null;
  context?: string | null;
};

// Package names are the only unbounded values in a table, so they are capped
// tighter than versions, counts and fixed labels.
const PACKAGE_NAME_COLUMN_CAP = 32;
const DEFAULT_COLUMN_CAP = 40;

// Root holds a package name too, but it is a secondary column, so it is capped
// below Package. 24 is a floor rather than a preference: unscoped roots such as
// "start-server-and-test +1" are themselves 24 characters with nothing to trim.
const ROOT_COLUMN_CAP = 24;

// Context is prose, so it gets room and is word-wrapped rather than truncated.
const CONTEXT_COLUMN_CAP = 60;

const dash = (value: string | null | undefined) => (value == null || value === "" ? "-" : value);

const TABLE_COLUMNS: TableColumn[] = [
  {
    name: "package",
    header: "Package",
    cap: PACKAGE_NAME_COLUMN_CAP,
    cell: row => ({ value: row.package, decorated: row.packageDecorated }),
  },
  { name: "version", header: "Version", cell: row => ({ value: dash(row.version) }) },
  {
    name: "severity",
    header: "Severity",
    cell: row => (row.severity
      ? { value: row.severity, decorated: formatSeverityLabel(row.severity) }
      : { value: "-" }),
  },
  {
    name: "type",
    header: "Type",
    cell: row => (row.relationship
      ? { value: row.relationship, decorated: formatRelationshipLabel(row.relationship) }
      : { value: "-" }),
  },
  {
    name: "root",
    header: "Root",
    cap: ROOT_COLUMN_CAP,
    cell: row => ({ value: dash(row.root) }),
  },
  {
    name: "usage",
    header: "Usage",
    cell: row => {
      if (!row.usage) return { value: "n/a", decorated: chalk.gray("n/a") };
      const value = row.usage.imported ? `${row.usage.files.length} file(s)` : "unused";
      return { value, decorated: row.usage.imported ? chalk.red(value) : chalk.green(value) };
    },
  },
  {
    name: "advisory",
    header: "Advisory",
    cell: row => {
      const value = dash(row.advisoryVersion);
      return { value, decorated: chalk.gray(value) };
    },
  },
  { name: "target", header: "Target", cell: row => ({ value: dash(row.target) }) },
  {
    name: "scanned",
    header: "Scanned",
    cell: row => {
      const value = row.scanned == null ? "-" : String(row.scanned);
      return { value, decorated: chalk.blue(value) };
    },
  },
  {
    name: "stillVulnerable",
    header: "Still\nvulnerable",
    cell: row => {
      if (row.stillVulnerable == null) return { value: "-", decorated: chalk.gray("-") };
      const value = String(row.stillVulnerable);
      return { value, decorated: row.stillVulnerable > 0 ? chalk.yellow(value) : chalk.green(value) };
    },
  },
  {
    name: "breaking",
    header: "Breaking?",
    cell: row => (row.breaking ? { value: "⚠", decorated: chalk.yellow("⚠") } : { value: "" }),
  },
  {
    name: "epss",
    header: "EPSS",
    cell: row => {
      const value = row.epss == null ? "-" : `${(row.epss * 100).toFixed(1)}%`;
      return { value, decorated: chalk.gray(value) };
    },
  },
  {
    name: "epssPriority",
    header: "EPSS\nPriority",
    cell: row => ({
      value: row.signal ? PRIORITY_SIGNAL_TABLE_LABELS[row.signal] : "-",
      decorated: formatPrioritySignal(row.signal ?? null),
    }),
  },
  {
    name: "context",
    header: "Context",
    cap: CONTEXT_COLUMN_CAP,
    wrapCap: CONTEXT_COLUMN_CAP,
    cell: row => {
      const value = dash(row.context);
      return { value, decorated: chalk.gray(value) };
    },
  },
];

/**
 * The findings table is the research view: everything we know, in one place.
 * The action tables are what you read to decide what to run, so they carry the
 * remediation columns only. Both are selections from TABLE_COLUMNS.
 */
const FINDINGS_TABLE_COLUMNS = [
  "package", "version", "severity", "type", "root", "usage",
  "advisory", "target", "scanned", "stillVulnerable", "breaking",
  "epss", "epssPriority",
];

// Both remediation tables draw the same columns. A direct upgrade and a parent
// upgrade are different rows, but showing them in differently shaped tables made
// the same section title render two different tables depending on the project.
const ACTION_TABLE_COLUMNS = [
  "package", "version", "usage", "advisory", "target",
  "scanned", "stillVulnerable", "breaking", "context",
];

// Usage is "n/a" on every row unless --usage or --only-used ran, so it is dropped
// rather than shown empty. Keyed off the data, which cannot disagree with the rows.
const USAGE_COLUMN = "usage";

function selectColumns(names: string[], showUsage: boolean): TableColumn[] {
  return TABLE_COLUMNS.filter(column => {
    if (!names.includes(column.name)) return false;
    return column.name !== USAGE_COLUMN || showUsage;
  });
}

function columnWidths(columns: TableColumn[], rows: TableRow[]): number[] {
  return columns.map(column =>
    Math.min(
      column.cap ?? DEFAULT_COLUMN_CAP,
      Math.max(cellWidth(column.header), ...rows.map(row => cellWidth(column.cell(row).value))),
    )
  );
}

function renderCells(columns: TableColumn[], row: TableRow): string[] {
  return columns.map(column => {
    const { value, decorated } = column.cell(row);
    return decorated ?? value;
  });
}

/** Draws a table from a column selection. `wrap` word-wraps instead of truncating. */
function printColumnTable(
  columns: TableColumn[],
  rows: TableRow[],
  widths: number[],
  options?: { wrap?: boolean; totalsRow?: TableRow },
): void {
  const line = (left: string, mid: string, right: string) =>
    left + widths.map(w => "─".repeat(w + 2)).join(mid) + right;

  console.log(line("┌", "┬", "┐"));
  console.log(renderRow(columns.map(column => column.header), widths));
  console.log(line("├", "┼", "┤"));

  for (const row of rows) {
    const cells = renderCells(columns, row);
    if (options?.wrap) {
      for (const outputRow of renderWrappedRow(cells, widths)) console.log(outputRow);
    } else {
      console.log(renderRow(cells, widths));
    }
  }

  if (options?.totalsRow) {
    console.log(line("├", "┼", "┤"));
    console.log(renderRow(renderCells(columns, options.totalsRow), widths));
  }

  console.log(line("└", "┴", "┘"));
}


/**
 * Drops the scope from a root that would otherwise be truncated.
 *
 * The end of the name is what distinguishes "@angular-devkit/build-angular" from
 * "@angular-devkit/build-webpack", so an ellipsis would eat the useful half. Only
 * roots past the cap are shortened, which is what keeps this unambiguous: short
 * scoped roots keep their scope, so "@angular/cli" and "@swc/cli" stay distinct
 * rather than both collapsing to "cli".
 */
function shortenRootSummary(summary: string): string {
  if (summary.length <= ROOT_COLUMN_CAP) return summary;
  const separator = summary.indexOf("/");
  if (!summary.startsWith("@") || separator === -1) return summary;
  return summary.slice(separator + 1);
}

/** Highest EPSS probability across a finding's advisories, or null when unscored. */
function bestEpssScore(finding: Finding): number | null {
  if (!finding.epssScores || finding.epssScores.length === 0) return null;
  return finding.epssScores.slice().sort((a, b) => b.percentile - a.percentile)[0]!.epss;
}

function findingToTableRow(
  finding: Finding,
  plan: SuggestedFixCommandPlan | null | undefined,
  skippedKeys: ReadonlySet<string> | undefined,
): TableRow {
  const isSkipped = !!skippedKeys?.has(`${finding.pkg.name}@${finding.pkg.version}`);
  // Prefer the version the fix plan will actually install. A package that is both
  // a direct finding and the parent of other findings needs a higher version than
  // its own advisory requires, and showing the lower one here contradicted the fix
  // command sitting a few lines above. For parent-update this is the child's
  // destination, not the parent's unchanged version stored on targetVersion.
  const planTarget = plan ? planVersionForFinding(plan, finding) : undefined;
  const ownFixVersion = finding.validatedFirstFixedVersion ?? finding.firstFixedVersion;
  const fixVersion = planTarget ?? ownFixVersion ?? null;
  return {
    package: finding.pkg.name,
    version: finding.pkg.version,
    severity: finding.severity,
    relationship: formatRelLabel(finding),
    root: shortenRootSummary(formatRootDependencySummary(finding)),
    usage: finding.usage ?? null,
    advisoryVersion: finding.firstFixedVersion ?? null,
    target: formatTargetDisplay(finding, fixVersion, isSkipped),
    // These count the versions walked above the installed one while checking the
    // advisory's hint, so they stand on their own even when the fix plan then
    // raises Target higher to cover a package's children. Blanking them whenever
    // that happened hid real validation on most rows of a typical scan.
    scanned: finding.validatedTargetScannedVersions,
    stillVulnerable: finding.validatedTargetKnownVulnerableVersions,
    breaking: !!fixVersion && isBreakingUpgrade(finding.pkg.version, fixVersion),
    epss: bestEpssScore(finding),
    signal: finding.epssScores && finding.epssScores.length > 0
      ? computePrioritySignal(finding.severity, finding.epssScores)
      : null,
  };
}

function formatTargetDisplay(finding: Finding, fixVersion: string | null, isSkipped: boolean): string {
  if (isSkipped && fixVersion) return chalk.gray(`${fixVersion} ⊘`);
  if (fixVersion) return fixVersion;
  if (finding.maliciousUnverifiable) return chalk.yellow("⚠ Unverifiable (private source)");
  if (finding.maliciousGitSource) {
    return chalk.yellow(finding.maliciousGitSourcePinned ? MAL_GIT_SOURCE_PINNED_DISPLAY : MAL_GIT_SOURCE_FLOATING_DISPLAY);
  }
  if (hasMaliciousAdvisory(finding.vulnerabilities)) return chalk.yellow("⚠ Malicious");
  return chalk.yellow("⚠ no fix");
}

/** A fix-plan target adapted onto the shared row shape. */
type FixTargetLike = {
  package: string;
  currentVersion?: string;
  targetVersion: string;
  kind?: SuggestedFixTarget["kind"];
  childPackage?: string;
  childTargetVersion?: string;
  scannedVersions?: number | null;
  knownVulnerableVersions?: number | null;
  advisoryVersion?: string | null;
  reason?: string;
  adjustmentNote?: string | null;
  usage?: { imported: boolean; files: string[] } | null;
};

function fixTargetContext(target: FixTargetLike): string | null {
  const childNote = formatParentUpdateChildNote(target);
  const reason = target.reason ?? target.adjustmentNote ?? null;
  if (childNote && reason) {
    if (target.childPackage && target.childTargetVersion
      && reason.includes(`${target.childPackage}@${target.childTargetVersion}`)) {
      return reason;
    }
    return `${childNote}. ${reason}`;
  }
  return childNote ?? reason;
}

function fixTargetToTableRow(target: FixTargetLike, context?: FixRowContext): TableRow {
  return {
    package: target.package,
    version: target.currentVersion ?? "-",
    severity: context?.severity ?? null,
    relationship: context?.relationship ?? null,
    root: context?.root ?? null,
    usage: target.usage ?? null,
    advisoryVersion: target.advisoryVersion ?? context?.advisoryVersion ?? null,
    target: chalk.cyan(target.targetVersion),
    // A parent-upgrade target carries no validation counts of its own, but the
    // finding it resolves does, and the action table is a filtered view of the
    // findings table: the same package must read the same on both.
    scanned: target.scannedVersions ?? context?.scanned ?? null,
    stillVulnerable: target.knownVulnerableVersions ?? context?.stillVulnerable ?? null,
    breaking: !!target.currentVersion && isBreakingUpgrade(target.currentVersion, target.targetVersion),
    epss: context?.epss ?? null,
    signal: context?.prioritySignal ?? null,
    context: fixTargetContext(target),
  };
}

/** The bold summary row under a fix table: only the validation counts carry values. */
function validationTotalsRow(summary: { checked: number; vulnerable: number }): TableRow {
  return {
    package: "Total",
    packageDecorated: chalk.bold("Total"),
    version: "-",
    scanned: summary.checked,
    stillVulnerable: summary.vulnerable,
  };
}

export function printTable(
  findings: Finding[],
  threshold: SeverityLabel | null,
  skippedKeys?: ReadonlySet<string>,
  plan?: SuggestedFixCommandPlan | null,
) {
  const columns = selectColumns(FINDINGS_TABLE_COLUMNS, findings.some(finding => !!finding.usage));
  const rows = findings.map(finding => findingToTableRow(finding, plan, skippedKeys));

  console.log("");
  // Every other block announces itself (Quick take, Suggested Fix Commands,
  // Coverage notes). This table was the only one arriving unlabelled, so it read
  // as a continuation of the fix plan above it rather than its own section.
  //
  // The filter belongs in the title rather than on its own line: as a separate
  // bold line it read as a second heading stacked under the first.
  console.log(chalk.bold.magenta(`Vulnerability findings${threshold ? ` (${threshold}+)` : ""}`));
  if (threshold) {
    console.log(chalk.gray("Use --all to show every finding."));
  }

  printColumnTable(columns, rows, columnWidths(columns, rows));

  if (findings.length > 0) {
    console.log("");
    console.log(chalk.bold("Prioritization signals (heuristic)"));
    console.log(chalk.gray("Triage hints only — not exploitability or runtime reachability proofs."));
    for (const finding of findings) {
      const values = formatContextualSignalValues(computeContextualSignals(finding));
      console.log(chalk.gray(`  ${finding.pkg.name}@${finding.pkg.version}  ${values}`));
    }
  }

  const maliciousFindings = findings.filter(f => hasMaliciousAdvisory(f.vulnerabilities));
  if (maliciousFindings.length > 0) {
    console.log("");
    console.log(chalk.bold.red("⚠ Malicious package advisory:"));
    for (const f of maliciousFindings) {
      const action = f.relationship === "direct"
        ? "Remove it from your dependencies immediately."
        : "Upgrade or remove the parent package that pulls it in.";
      if (f.maliciousUnverifiable) {
        console.log(chalk.yellow(`  · ${f.pkg.name}@${f.pkg.version} - Unverifiable (private source) - ${action}`));
      } else if (f.maliciousGitSource) {
        const msg = f.maliciousGitSourcePinned ? MAL_GIT_SOURCE_PINNED_MESSAGE : MAL_GIT_SOURCE_FLOATING_MESSAGE;
        const url = f.pkg.resolvedUrl ? ` (${f.pkg.resolvedUrl})` : "";
        console.log(chalk.yellow(`  · ${f.pkg.name}@${f.pkg.version}${url} - ${msg}`));
      } else {
        console.log(chalk.red(`  · ${f.pkg.name}@${f.pkg.version} - ${action}`));
      }
    }
  }

  if (skippedKeys && skippedKeys.size > 0 && findings.some(f => skippedKeys.has(`${f.pkg.name}@${f.pkg.version}`))) {
    console.log(chalk.gray("⊘ Advisory hint only — no automated fix command could be generated. Run --report to view detailed skip reasons."));
  }

  if (threshold) {
    console.log(chalk.gray("Tip: use --all to include low findings, or --min-severity high to focus only on urgent issues."));
  }
}

/**
 * Builds the one-sentence verdict both output modes close with.
 *
 * Compact and verbose used to construct this separately, 350 lines apart, and had
 * drifted: compact reported critical+high while verbose reported every finding, so
 * the same scan closed with "7 urgent issues" or "11 vulnerabilities" depending on
 * the flag. Verbose's noun was wrong too - findings are vulnerable packages, and
 * that scan carried 94 advisories across its 11 packages (#1168).
 */
function buildScanVerdict(
  findingCount: number,
  critical: number,
  high: number,
): { text: string; urgent: boolean } {
  const urgentCount = critical + high;
  const packages = `${findingCount} vulnerable ${pluralize(findingCount, "package")}`;
  // Only name the severities actually present. "(0 critical, 1 high)" reads as noise.
  const breakdown = [
    critical > 0 ? `${critical} critical` : null,
    high > 0 ? `${high} high` : null,
  ].filter(Boolean).join(", ");
  const urgentNote = urgentCount > 0 ? `, ${urgentCount} urgent (${breakdown})` : "";
  return { text: `${packages}${urgentNote}`, urgent: urgentCount > 0 };
}

export function printFinalStatus(findings: Finding[], overrideCount = 0, completeness?: ScanCompleteness) {
  console.log("");
  console.log(chalk.gray("────────────────────────────────"));

  const { hasDetectionGap, hasRemediationGap } = getCompletenessImpact(completeness);
  const overrideSuffix = overrideCount > 0
    ? `, ${overrideCount} override hygiene ${pluralize(overrideCount, "issue")}`
    : "";

  if (findings.length === 0) {
    if (hasDetectionGap) {
      const overrideNote = overrideCount > 0
        ? ` ${overrideCount} override hygiene ${pluralize(overrideCount, "issue")} detected.`
        : "";
      console.log(chalk.yellow(`⚠ Partial scan: vulnerability findings may be incomplete.${overrideNote}`));
    } else if (overrideCount > 0) {
      console.log(chalk.yellow(`▲ Scan complete. No known vulnerabilities found, but ${overrideCount} override hygiene ${pluralize(overrideCount, "issue")} detected.`));
    } else {
      console.log(chalk.greenBright("✔ Scan complete. No known vulnerabilities found."));
    }
  } else {
    const criticalCount = findings.filter(f => f.severity === "critical").length;
    const highCount = findings.filter(f => f.severity === "high").length;
    const verdict = buildScanVerdict(findings.length, criticalCount, highCount);
    const action = verdict.urgent ? "Start with the priority fixes above." : "Review the suggested fix plan above.";
    const renderStatus = verdict.urgent ? chalk.redBright : chalk.yellow;

    if (hasDetectionGap) {
      console.log(renderStatus(
        `⚠ Partial scan: ${verdict.text}${overrideSuffix}. Vulnerability findings may be incomplete. ${action}`
      ));
    } else if (verdict.urgent) {
      console.log(chalk.redBright(`✖ Scan complete. ${verdict.text}${overrideSuffix}. ${action}`));
    } else {
      console.log(chalk.yellow(`▲ Scan complete. ${verdict.text}${overrideSuffix}. ${action}`));
    }
  }

  if (hasRemediationGap) {
    console.log(chalk.yellow("⚠ Remediation guidance is incomplete."));
  }
  printIncompleteDiagnostics(completeness);
}

export function printOverrideHint(): void {
  console.log("💡 " + chalk.gray("Tip:") + " override entries detected - run with --check-overrides to audit them for stale or broken overrides.");
}

// A cell may contain newlines, which render as extra physical lines within the
// same logical row. This is what keeps the table width bounded: a finding with
// twelve advisory IDs is twelve short lines rather than one 628-character cell
// that has to be truncated into uselessness.
// One searchable advisory ID plus a count of the rest. The full list belongs in
// --json, --sarif and the HTML report, where it is not competing for terminal
// width and each ID is a link. Joined into the table it ran to 628 characters on
// a real project, and truncated it left a single usable ID followed by a stump.
function renderRow(cells: string[], widths: number[]) {
  const columnLines = cells.map(cell => String(cell).split("\n"));
  const height = Math.max(1, ...columnLines.map(lines => lines.length));

  const physicalLines: string[] = [];
  for (let line = 0; line < height; line++) {
    const formatted = columnLines.map((lines, i) => {
      const truncated = truncate(lines[line] ?? "", widths[i]!);
      const visible = stripAnsi(truncated);
      return ` ${truncated}${" ".repeat(Math.max(0, widths[i]! - visible.length))} `;
    });
    physicalLines.push("│" + formatted.join("│") + "│");
  }
  return physicalLines.join("\n");
}

// Width of the longest single line in a cell, not of the whole cell.
function cellWidth(value: unknown): number {
  return Math.max(...String(value).split("\n").map(line => stripAnsi(line).length));
}

function truncate(value: string, width: number) {
  const plain = stripAnsi(value);
  if (plain.length <= width) return value;
  return plain.slice(0, Math.max(0, width - 1)) + "…";
}

function renderWrappedRow(cells: string[], widths: number[]) {
  const wrappedCells = cells.map((cell, i) => wrapCell(cell, widths[i]));
  const rowHeight = Math.max(...wrappedCells.map(cellLines => cellLines.length));
  const rows: string[] = [];

  for (let lineIndex = 0; lineIndex < rowHeight; lineIndex++) {
    const formatted = wrappedCells.map((cellLines, i) => {
      const value = cellLines[lineIndex] ?? "";
      const visible = stripAnsi(value);
      return ` ${value}${" ".repeat(Math.max(0, widths[i] - visible.length))} `;
    });
    rows.push("│" + formatted.join("│") + "│");
  }

  return rows;
}

function wrapCell(value: string, width: number): string[] {
  const plain = stripAnsi(value);
  if (plain.length <= width) return [value];
  if (width <= 0) return [""];

  const lines: string[] = [];
  let remaining = plain.trim();

  while (remaining.length > width) {
    let breakAt = remaining.lastIndexOf(" ", width);
    if (breakAt <= 0) breakAt = width;
    lines.push(remaining.slice(0, breakAt).trimEnd());
    remaining = remaining.slice(breakAt).trimStart();
  }

  if (remaining.length > 0) {
    lines.push(remaining);
  }

  return lines.length > 0 ? lines : [""];
}

export function printCompactOutput(
  findings: Finding[],
  scanInput?: ScanInput,
  options?: {
    offline?: boolean;
    all?: boolean;
    subfolder?: string;
    packageManager?: string;
    completeness?: ScanCompleteness;
    licenseFindings?: LicenseFinding[];
    licenseLimitedToDirectOnly?: boolean;
  },
) {
  console.log("");
  const { hasDetectionGap, hasRemediationGap } = getCompletenessImpact(options?.completeness);
  if (options?.packageManager) {
    console.log(chalk.gray("Package manager: ") + options.packageManager);
  }

  if (findings.length === 0) {
    if (hasDetectionGap) {
      console.log(chalk.yellow("⚠ Partial scan: vulnerability findings may be incomplete."));
    } else {
      console.log(chalk.greenBright("✔ Scan complete. No known vulnerabilities found."));
    }
    if (hasRemediationGap) {
      console.log(chalk.yellow("⚠ Remediation guidance is incomplete."));
    }
    if (options?.completeness?.complete === false) {
      printIncompleteDiagnostics(options.completeness);
    } else {
      console.log("");
    }
    return;
  }

  // Vulnerabilities found section
  console.log("────────────────────────────────");
  console.log(chalk.bold("📦 Vulnerabilities found"));
  console.log("────────────────────────────────\n");

  // Reuse shared display selection logic so compact mode does not silently
  // drop direct unknown-severity findings.
  const urgentFindings = selectFindingsForCompact(findings, { urgentLimit: COMPACT_FINDING_BLOCK_LIMIT });

  for (const finding of urgentFindings) {
    const sevLabel = finding.severity.toUpperCase().padEnd(8);
    const typeLabel = finding.relationship === "direct"
      ? `Direct dependency${finding.pkg.dev === true ? " · dev" : ""}`
      : finding.relationship === "transitive"
        ? `Transitive dependency${finding.pkg.dev === true ? " · dev" : ""}`
        : "Unknown dependency";
        
    let usageContext = "";
    if (finding.usage) {
      if (finding.usage.imported) {
        usageContext = chalk.red(` (imported in ${finding.usage.files.length} ${pluralize(finding.usage.files.length, "file")})`);
      } else {
        usageContext = chalk.green(` (no direct import found)`);
      }
    }
    
    console.log(`${formatSeverityLabel(sevLabel)} ${chalk.whiteBright(finding.pkg.name)}@${finding.pkg.version}`);
    console.log(`            ${typeLabel}${usageContext}`);
    console.log(`            ${chalk.gray(formatContextualSignalsLine(computeContextualSignals(finding)))}`);
    if (finding.epssScores && finding.epssScores.length > 0) {
      const best = finding.epssScores.slice().sort((a, b) => b.percentile - a.percentile)[0]!;
      const pct = (best.epss * 100).toFixed(1);
      const top = ((1 - best.percentile) * 100);
      const topStr = top < 0.01 ? "<0.01" : top < 1 ? top.toFixed(2) : top.toFixed(1);
      console.log(`            ${chalk.gray(`EPSS: ${pct}% exploitation probability - ${best.cve} (top ${topStr}% of all CVEs)`)}`);
      const priority = computePrioritySignal(finding.severity, finding.epssScores);
      if (priority === "fix_now") {
        console.log(`            ${chalk.red(PRIORITY_SIGNAL_LABELS.fix_now)} - ${PRIORITY_SIGNAL_DESCRIPTIONS[priority]}`);
      }
    }

    const isMalicious = hasMaliciousAdvisory(finding.vulnerabilities);
    if (isMalicious) {
      if (finding.maliciousUnverifiable) {
        console.log(`            ${chalk.yellow(`⚠ Unverifiable (private source) - ${MAL_PRIVATE_REGISTRY_COMPACT_MESSAGE}`)}`);
      } else if (finding.maliciousGitSource) {
        const url = finding.pkg.resolvedUrl ? ` Source: ${finding.pkg.resolvedUrl}` : "";
        console.log(`            ${chalk.yellow(`⚠ ${MAL_GIT_SOURCE_COMPACT_MESSAGE}${url}`)}`);
      } else {
        const action = finding.relationship === "direct"
          ? "Remove this package from your dependencies immediately."
          : "Upgrade or remove the parent package that pulls it in.";
        console.log(`            ${chalk.red(`⚠ Malicious: ${action}`)}`);
      }
    } else if (finding.recommendedNpmTransitiveRemediation?.kind === "update-parent-within-range") {
      console.log(
        `            ${chalk.gray(`Fix: run \`npm install\` - ${finding.recommendedNpmTransitiveRemediation.package} already permits a safe version`)}`,
      );
    } else if (finding.recommendedParentUpgrade) {
      console.log(
        `            ${chalk.gray(`Fix: upgrade ${finding.recommendedParentUpgrade.package} to ${finding.recommendedParentUpgrade.targetVersion}`)}`,
      );
    } else if (finding.firstFixedVersion) {
      const displayFixVersion = finding.validatedFirstFixedVersion ?? finding.firstFixedVersion;
      let action: string;
      if (finding.relationship === "direct") {
        action = `upgrade to ${displayFixVersion}`;
      } else {
        const parent = getPrimaryParent(finding);
        action = parent
          ? `Upgrade ${parent} — check for release resolving ${finding.pkg.name} to ${displayFixVersion}+`
          : `No dependency path found — inspect lockfile to identify which package pulls in ${finding.pkg.name}`;
      }
      console.log(`            ${chalk.gray(`Fix: ${action}`)}`);
    } else {
      let action: string;
      if (finding.relationship === "direct") {
        action = "review and upgrade directly";
      } else {
        const parent = getPrimaryParent(finding);
        action = parent
          ? `Upgrade ${parent} to resolve ${finding.pkg.name}`
          : `No dependency path found — inspect lockfile to identify which package pulls in ${finding.pkg.name}`;
      }
      console.log(`            ${chalk.gray(`Fix: ${action}`)}`);
    }
    console.log("");
  }

  const findingTruncationNotice = formatCompactFindingTruncationNotice(
    urgentFindings.length,
    findings.length,
  );
  if (findingTruncationNotice && !options?.all) {
    console.log(chalk.gray(findingTruncationNotice));
    console.log("");
  }

  const plan = scanInput ? buildSuggestedFixCommandPlan(findings, scanInput, options) : null;

  if (plan) {
    if (plan?.sections.length) {
      console.log("────────────────────────────────");
      console.log(chalk.bold.yellow("🛠  Suggested Fix Commands"));
      console.log("────────────────────────────────\n");
      console.log(`${chalk.gray("Detected package manager:")} ${chalk.cyan(plan.packageManager)} ${chalk.gray(`(${plan.sourceLabel})`)}`);
      console.log(formatFixCommandSummary(plan));
      const compactValidationSummary = summarizeAdjustedValidation(plan.targets);
      if (compactValidationSummary.checked > 0) {
        console.log(
          chalk.gray(
            `Validation: scanned ${compactValidationSummary.checked} package ${pluralize(compactValidationSummary.checked, "version")}; ${compactValidationSummary.vulnerable} ${pluralize(compactValidationSummary.vulnerable, "is", "are")} still known vulnerable.`,
          ),
        );
      }
      console.log("");
      const shownSections = plan.sections.slice(0, COMPACT_COMMAND_GROUP_LIMIT);
      for (const section of shownSections) {
        console.log(`${section.title}`);
        for (const target of section.targets) {
          if (section.kind === "direct-adjusted" && target.adjustmentNote) {
            console.log(chalk.gray(`  Note: ${target.adjustmentNote}`));
          }
          printCooldownWarning(target);
        }
        console.log(renderCommandCallout(section.command, section.targets));
            console.log("");
      }
      const commandGroupTruncationNotice = formatCompactCommandGroupTruncationNotice(
        plan.sections.slice(COMPACT_COMMAND_GROUP_LIMIT),
      );
      if (commandGroupTruncationNotice) {
        console.log(chalk.gray(commandGroupTruncationNotice));
        console.log("");
      }
    }
  }

  if (options?.licenseFindings) {
    console.log(renderLicenseFindings(options.licenseFindings, { limitedToDirectOnly: !!options.licenseLimitedToDirectOnly }));
    console.log("");
    console.log("");
  }

  // Summary
  console.log("────────────────────────────────");
  console.log("Summary");
  console.log("────────────────────────────────\n");

  const counts = {
    critical: findings.filter(f => f.severity === "critical").length,
    high: findings.filter(f => f.severity === "high").length,
    medium: findings.filter(f => f.severity === "medium").length,
    low: findings.filter(f => f.severity === "low").length,
    unknown: findings.filter(f => f.severity === "unknown").length
  };

  const direct = findings.filter(f => f.relationship === "direct").length;
  const transitive = findings.filter(f => f.relationship === "transitive").length;

  const parts: string[] = [];
  if (counts.critical > 0) parts.push(chalk.redBright(`${counts.critical} critical`));
  if (counts.high > 0) parts.push(chalk.magenta(`${counts.high} high`));
  if (counts.medium > 0) parts.push(chalk.yellow(`${counts.medium} medium`));
  if (counts.low > 0) parts.push(chalk.green(`${counts.low} low`));
  if (counts.unknown > 0) parts.push(chalk.gray(`${counts.unknown} unknown`));

  const compactCVEs = countUniqueAdvisories(findings);
  const compactPkgLabel = findings.length === 1 ? "package" : "packages";
  const compactCveLabel = compactCVEs === 1 ? "CVE" : "CVEs";
  console.log(
    `${chalk.whiteBright(String(findings.length))} ${compactPkgLabel}` +
    chalk.gray(" · ") +
    `${chalk.whiteBright(String(compactCVEs))} ${compactCveLabel}`
  );
  console.log(parts.join(chalk.gray(" · ")));
  console.log(
    `${chalk.cyan(String(direct))} ${chalk.white("direct")}` +
    `${chalk.gray(" · ")}` +
    `${chalk.cyan(String(transitive))} ${chalk.white("transitive")}`
  );
  const compactProdSplit = countProdFindings(findings);
  if (compactProdSplit !== null) {
    console.log(chalk.gray(`  └ ${compactProdSplit.prodTotal} of ${compactProdSplit.total} findings in prod dependencies`));
  }

  if (options?.licenseFindings && options.licenseFindings.length > 0) {
    const lHigh = options.licenseFindings.filter(f => f.severity === "high").length;
    const lMed = options.licenseFindings.filter(f => f.severity === "medium").length;
    const lParts: string[] = [];
    if (lHigh > 0) lParts.push(chalk.red(`${lHigh} high`));
    if (lMed > 0) lParts.push(chalk.yellow(`${lMed} medium`));
    console.log(chalk.gray("⚖  Licenses: ") + lParts.join(chalk.gray(" · ")) + chalk.gray(" (informational)"));
  }

  const maliciousCompact = findings.filter(f => hasMaliciousAdvisory(f.vulnerabilities));
  if (maliciousCompact.length > 0 && !options?.all) {
    console.log("");
    console.log(chalk.bold.red("⚠ Malicious package advisory:"));
    for (const f of maliciousCompact) {
      if (f.maliciousUnverifiable) {
        console.log(chalk.yellow(`  · ${f.pkg.name}@${f.pkg.version} - Unverifiable (private source) - ${MAL_PRIVATE_REGISTRY_LEGEND_MESSAGE}`));
      } else if (f.maliciousGitSource) {
        console.log(chalk.yellow(`  · ${f.pkg.name}@${f.pkg.version} - Git source - ${MAL_GIT_SOURCE_LEGEND_MESSAGE}`));
      } else {
        const action = f.relationship === "direct"
          ? "Remove it from your dependencies immediately."
          : "Upgrade or remove the parent package that pulls it in.";
        console.log(chalk.red(`  · ${f.pkg.name}@${f.pkg.version} - ${action}`));
      }
    }
  }

  if (options?.all) {
    printTable(findings, null, undefined, plan);
  } else {
    console.log("");
  }

  // Footer
  const verdict = buildScanVerdict(findings.length, counts.critical, counts.high);
  const renderStatus = verdict.urgent ? chalk.redBright : chalk.yellow;
  if (hasDetectionGap) {
    console.log(renderStatus(`⚠ Partial scan: ${verdict.text}. Vulnerability findings may be incomplete.`));
  } else if (verdict.urgent) {
    console.log(chalk.redBright(`✖ Scan complete. ${verdict.text}.`));
  } else {
    console.log(chalk.yellow(`▲ Scan complete. ${verdict.text}.`));
  }
  printIncompleteDiagnostics(options?.completeness);
  if (hasRemediationGap) {
    console.log(chalk.yellow("⚠ Remediation guidance is incomplete."));
  }
  if (!options?.all) {
    console.log(chalk.gray(`Run with ${chalk.whiteBright("--verbose")} for fix plan, paths, and full table.`));
  }
  if (options?.completeness?.complete !== false) {
    console.log("");
  }
}

export function printIncompleteDiagnostics(completeness?: ScanCompleteness): void {
  if (!completeness || completeness.complete) return;
  for (const diag of completeness.diagnostics) {
    const color = diag.impact === "detection" ? chalk.yellow : chalk.gray;
    console.log(color(`⚠ ${diag.message}`));
  }
  console.log("");
  console.log(chalk.gray("Resolve the issues above and re-run the scan."));
}

function renderSeverityTable(counts: { critical: number; high: number; medium: number; low: number; unknown: number }): string {
  const labels = ["Critical", "High", "Medium", "Low", "Unknown"];
  const coloredValues = [
    chalk.redBright(String(counts.critical)),
    chalk.red(String(counts.high)),
    chalk.yellow(String(counts.medium)),
    chalk.blueBright(String(counts.low)),
    chalk.magenta(String(counts.unknown)),
  ];
  const rawValues = [
    String(counts.critical),
    String(counts.high),
    String(counts.medium),
    String(counts.low),
    String(counts.unknown),
  ];
  const widths = labels.map((label, i) => Math.max(label.length, rawValues[i].length));
  const line = (left: string, mid: string, right: string) =>
    left + widths.map(w => "─".repeat(w + 2)).join(mid) + right;
  const pad = (text: string, raw: string, width: number) => {
    const pad = width - raw.length;
    const left = Math.floor(pad / 2);
    const right = pad - left;
    return " ".repeat(left + 1) + text + " ".repeat(right + 1);
  };
  const headerRow = "│" + labels.map((label, i) => ` ${label.padStart(Math.floor((widths[i] - label.length) / 2) + label.length).padEnd(widths[i])} `).join("│") + "│";
  const valueRow = "│" + coloredValues.map((val, i) => pad(val, rawValues[i], widths[i])).join("│") + "│";
  return [line("┌", "┬", "┐"), headerRow, line("├", "┼", "┤"), valueRow, line("└", "┴", "┘")].join("\n");
}

function colorFixSectionTitle(
  severity: SeverityLabel,
  title: string,
) {
  if (severity === "critical") return chalk.redBright(title);
  if (severity === "high") return chalk.magenta(title);
  if (severity === "medium") return chalk.yellow(title);
  if (severity === "low") return chalk.green(title);
  return chalk.gray(title);
}

function formatFixCommandSummary(
  plan: ReturnType<typeof buildSuggestedFixCommandPlan>,
) {
  if (!plan) return "";

  const packageCount = plan.targets.length;
  const sectionCount = plan.sections.length;
  const severityCounts = new Map<SeverityLabel, number>();

  for (const section of plan.sections) {
    severityCounts.set(section.severity, (severityCounts.get(section.severity) ?? 0) + 1);
  }

  const severitySummary = (["critical", "high", "medium", "low", "unknown"] as SeverityLabel[])
    .filter(severity => (severityCounts.get(severity) ?? 0) > 0)
    .map(severity => `${severityCounts.get(severity)} ${severity}`)
    .join(", ");

  const packageLabel = packageCount === 1 ? "package" : "packages";
  const sectionLabel = sectionCount === 1 ? "group" : "groups";

  return `${sectionCount} command ${sectionLabel} ready across ${packageCount} ${packageLabel}${severitySummary ? ` (${severitySummary})` : ""}.`;
}

// No table carries a Published column, so the publish date rides on the command
// itself in both verbose and compact output, as it did before the column existed.
function renderCommandCallout(command: string, targets?: SuggestedFixTarget[]) {
  const display = targets ? formatFixCommandWithPublishDates(command, targets) : command;
  return chalk.bold.cyan(`> ${display}`);
}


function summarizeAdjustedValidation(
  targets: Array<{ scannedVersions?: number | null; knownVulnerableVersions?: number | null }>,
): { checked: number; vulnerable: number } {
  let checked = 0;
  let vulnerable = 0;
  for (const target of targets) {
    if (target.scannedVersions === null || target.scannedVersions === undefined) continue;
    checked += target.scannedVersions;
    vulnerable += target.knownVulnerableVersions ?? 0;
  }
  return { checked, vulnerable };
}


/**
 * Finding-level facts for a package that appears in the fix plan.
 *
 * A fix target names a package and a version; the severity, type, root and EPSS
 * live on the findings it resolves. Values are raw rather than pre-formatted so
 * the shared column registry does the rendering, which is what keeps a column
 * identical wherever it appears.
 */
type FixRowContext = {
  severity: SeverityLabel;
  relationship: string;
  root: string;
  epss: number | null;
  prioritySignal: PrioritySignal | null;
  advisoryVersion: string | null;
  scanned: number | null;
  stillVulnerable: number | null;
};

function buildFixRowContexts(findings: Finding[]): Map<string, FixRowContext> {
  const byPackage = new Map<string, Finding[]>();
  for (const finding of findings) {
    const list = byPackage.get(finding.pkg.name);
    if (list) list.push(finding);
    else byPackage.set(finding.pkg.name, [finding]);
  }

  const contexts = new Map<string, FixRowContext>();
  for (const [name, group] of byPackage) {
    // The package's own finding describes Type and Root; fall back to the
    // first of the group when the package only appears as somebody else's parent.
    const own = group.find(f => f.relationship === "direct") ?? group[0]!;
    const worst = group.reduce((a, b) => (severityOrder[b.severity] > severityOrder[a.severity] ? b : a));

    let bestEpss: number | null = null;
    let bestSignal: PrioritySignal | null = null;
    for (const finding of group) {
      if (!finding.epssScores || finding.epssScores.length === 0) continue;
      const top = finding.epssScores.slice().sort((a, b) => b.percentile - a.percentile)[0]!;
      if (bestEpss === null || top.epss > bestEpss) {
        bestEpss = top.epss;
        bestSignal = computePrioritySignal(finding.severity, finding.epssScores);
      }
    }

    contexts.set(name, {
      severity: worst.severity,
      relationship: formatRelLabel(own),
      root: shortenRootSummary(formatRootDependencySummary(own)),
      epss: bestEpss,
      prioritySignal: bestSignal,
      advisoryVersion: own.firstFixedVersion ?? null,
      scanned: own.validatedTargetScannedVersions ?? null,
      stillVulnerable: own.validatedTargetKnownVulnerableVersions ?? null,
    });
  }
  return contexts;
}

/**
 * The one remediation table. Every fix-plan section draws exactly this.
 *
 * Context is word-wrapped rather than truncated because it is prose, so the whole
 * table wraps. An adjustment note already represented by the Scanned and Still
 * vulnerable columns is dropped rather than repeated underneath.
 */
/**
 * Totals row for a set of rendered rows, or undefined when nothing was scanned.
 *
 * Parent upgrades carry no validation counts, so a totals row across only those
 * would read 0 of 0 and mean nothing.
 */
function summarizeRenderedValidation(rows: TableRow[]): TableRow | undefined {
  const scanned = rows.filter(row => row.scanned != null);
  if (scanned.length === 0) return undefined;
  return validationTotalsRow({
    checked: scanned.reduce((total, row) => total + (row.scanned ?? 0), 0),
    vulnerable: scanned.reduce((total, row) => total + (row.stillVulnerable ?? 0), 0),
  });
}

function printActionTargetsTable(
  targets: Array<FixTargetLike & { adjustmentNote?: string | null; severity?: SeverityLabel }>,
  remainingNotes: string[],
  widthsOverride?: number[],
  contexts?: Map<string, FixRowContext>,
  showUsage = true,
): void {
  for (const target of targets) {
    if (!target.adjustmentNote) continue;
    const isCountedVulnerabilityNote =
      target.scannedVersions !== null &&
      target.scannedVersions !== undefined &&
      target.adjustmentNote.includes("is still known vulnerable for");
    if (!isCountedVulnerabilityNote) remainingNotes.push(target.adjustmentNote);
  }

  if (targets.length === 0) return;

  const columns = selectColumns(ACTION_TABLE_COLUMNS, showUsage);
  const rows = targets.map(target => fixTargetToTableRow(target, contexts?.get(target.package)));
  // Totalled from the rendered rows, not the raw targets, so the total always adds
  // up the numbers printed above it. A target with no counts of its own can still
  // resolve them from its finding, and summing the targets missed exactly those.
  const totalsRow = summarizeRenderedValidation(rows);
  const widths = widthsOverride ?? columnWidths(columns, totalsRow ? [...rows, totalsRow] : rows);

  printColumnTable(columns, rows, widths, { wrap: true, totalsRow });
}

/**
 * One width set for every remediation table in the run.
 *
 * Both tables draw the same columns, so they must also be measured together:
 * sizing them separately produced 134 and 151 in the same Nest report. Every
 * target is measured regardless of section kind, because the renderer splits by
 * target kind and anything left unmeasured gets truncated.
 */
function computeSharedActionTableWidths(
  sections: Array<{ targets: FixTargetLike[] }>,
  showUsage: boolean,
  contexts?: Map<string, FixRowContext>,
): number[] | undefined {
  const allTargets = sections.flatMap(section => section.targets);
  if (allTargets.length === 0) return undefined;

  const columns = selectColumns(ACTION_TABLE_COLUMNS, showUsage);
  // Built with the same contexts the renderer uses, so a count resolved from a
  // finding is measured rather than truncated when it is wider than the target's.
  const rows: TableRow[] = allTargets.map(target => fixTargetToTableRow(target, contexts?.get(target.package)));
  const totalsRow = summarizeRenderedValidation(rows);
  if (totalsRow) rows.push(totalsRow);

  return columnWidths(columns, rows);
}
