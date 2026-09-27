"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SEVERITY_ORDER = void 0;
exports.reachesFailOn = reachesFailOn;
exports.failingGateSummary = failingGateSummary;
exports.formatSeverityLabel = formatSeverityLabel;
exports.countBySeverity = countBySeverity;
exports.severityToSarifLevel = severityToSarifLevel;
var chalk_js_1 = require("./chalk.js");
var constants_js_1 = require("../constants.js");
var severity_js_1 = require("../osv/severity.js");
exports.SEVERITY_ORDER = ["critical", "high", "medium", "low", "unknown", "none"];
function reachesFailOn(findings, failOn) {
    if (!failOn)
        return false;
    var failLevel = (0, severity_js_1.normalizeSeverity)(failOn);
    return findings.some(function (f) { return constants_js_1.severityOrder[f.severity] >= constants_js_1.severityOrder[failLevel]; });
}
// One line that names what tripped the --fail-on gate, so a red CI job says why
// it is red. The gate ORs three finding classes (CVE, override hygiene,
// maintenance risk) and none of the rendered output mentioned the gate before,
// which read as a broken exit code. Returns null when the gate would not fire,
// so callers can log unconditionally without changing clean-run output.
function failingGateSummary(classes, failOn) {
    if (!failOn)
        return null;
    var failLevel = (0, severity_js_1.normalizeSeverity)(failOn);
    var parts = [];
    for (var _i = 0, classes_1 = classes; _i < classes_1.length; _i++) {
        var _a = classes_1[_i], label = _a.label, findings = _a.findings;
        var count = findings.filter(function (f) { return constants_js_1.severityOrder[f.severity] >= constants_js_1.severityOrder[failLevel]; }).length;
        if (count > 0)
            parts.push("".concat(count, " ").concat(label, " ").concat(count === 1 ? "finding" : "findings"));
    }
    if (parts.length === 0)
        return null;
    return "Failing: ".concat(parts.join(", "), " at or above ").concat(failLevel, " (--fail-on ").concat(failLevel, ").");
}
function formatSeverityLabel(severity) {
    var lower = severity.toLowerCase();
    if (lower === "critical")
        return chalk_js_1.chalk.redBright(severity);
    if (lower === "high")
        return chalk_js_1.chalk.red(severity);
    if (lower === "medium")
        return chalk_js_1.chalk.yellow(severity);
    if (lower === "low")
        return chalk_js_1.chalk.blueBright(severity);
    if (lower === "unknown")
        return chalk_js_1.chalk.magenta(severity);
    return severity;
}
function countBySeverity(findings) {
    var counts = {
        none: 0,
        low: 0,
        medium: 0,
        high: 0,
        critical: 0,
        unknown: 0,
    };
    for (var _i = 0, findings_1 = findings; _i < findings_1.length; _i++) {
        var finding = findings_1[_i];
        counts[finding.severity] += 1;
    }
    return counts;
}
function severityToSarifLevel(severity) {
    if (severity === "critical" || severity === "high")
        return "error";
    if (severity === "medium")
        return "warning";
    return "note";
}
