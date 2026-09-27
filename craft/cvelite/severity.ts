import type { SeverityLabel } from "../types.js";
import { chalk } from "./chalk.js";
import { severityOrder } from "../constants.js";
import { normalizeSeverity } from "../osv/severity.js";

export const SEVERITY_ORDER: SeverityLabel[] = ["critical", "high", "medium", "low", "unknown", "none"];

export function reachesFailOn<T extends { severity: SeverityLabel }>(
  findings: ReadonlyArray<T>,
  failOn: string,
): boolean {
  if (!failOn) return false;
  const failLevel = normalizeSeverity(failOn);
  return findings.some((f) => severityOrder[f.severity] >= severityOrder[failLevel]);
}

// One line that names what tripped the --fail-on gate, so a red CI job says why
// it is red. The gate ORs three finding classes (CVE, override hygiene,
// maintenance risk) and none of the rendered output mentioned the gate before,
// which read as a broken exit code. Returns null when the gate would not fire,
// so callers can log unconditionally without changing clean-run output.
export function failingGateSummary(
  classes: ReadonlyArray<{ label: string; findings: ReadonlyArray<{ severity: SeverityLabel }> }>,
  failOn: string,
): string | null {
  if (!failOn) return null;
  const failLevel = normalizeSeverity(failOn);
  const parts: string[] = [];
  for (const { label, findings } of classes) {
    const count = findings.filter((f) => severityOrder[f.severity] >= severityOrder[failLevel]).length;
    if (count > 0) parts.push(`${count} ${label} ${count === 1 ? "finding" : "findings"}`);
  }
  if (parts.length === 0) return null;
  return `Failing: ${parts.join(", ")} at or above ${failLevel} (--fail-on ${failLevel}).`;
}

export function formatSeverityLabel(severity: string): string {
  const lower = severity.toLowerCase();
  if (lower === "critical") return chalk.redBright(severity);
  if (lower === "high") return chalk.red(severity);
  if (lower === "medium") return chalk.yellow(severity);
  if (lower === "low") return chalk.blueBright(severity);
  if (lower === "unknown") return chalk.magenta(severity);
  return severity;
}

export function countBySeverity<T extends { severity: SeverityLabel }>(findings: T[]): Record<SeverityLabel, number> {
  const counts: Record<SeverityLabel, number> = {
    none: 0,
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
    unknown: 0,
  };
  for (const finding of findings) {
    counts[finding.severity] += 1;
  }
  return counts;
}

export function severityToSarifLevel(severity: SeverityLabel): "error" | "warning" | "note" {
  if (severity === "critical" || severity === "high") return "error";
  if (severity === "medium") return "warning";
  return "note";
}
