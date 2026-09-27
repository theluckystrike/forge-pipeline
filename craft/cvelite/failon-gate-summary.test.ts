import { failingGateSummary } from "../../src/utils/severity.js";

describe("failingGateSummary", () => {
  it("names the class and threshold for the maintainer reproduction in issue #1000", () => {
    const line = failingGateSummary(
      [{ label: "override hygiene", findings: [{ severity: "low" }] }],
      "low",
    );
    expect(line).toBe(
      "Failing: 1 override hygiene finding at or above low (--fail-on low).",
    );
  });

  it("counts only findings that meet or exceed the threshold", () => {
    const line = failingGateSummary(
      [
        { label: "vulnerability", findings: [{ severity: "critical" }, { severity: "low" }] },
        { label: "override hygiene", findings: [{ severity: "low" }] },
      ],
      "high",
    );
    expect(line).toBe(
      "Failing: 1 vulnerability finding at or above high (--fail-on high).",
    );
  });

  it("joins multiple tripped classes with correct pluralization", () => {
    const line = failingGateSummary(
      [
        { label: "vulnerability", findings: [{ severity: "high" }, { severity: "high" }] },
        { label: "maintenance risk", findings: [{ severity: "high" }] },
      ],
      "medium",
    );
    expect(line).toBe(
      "Failing: 2 vulnerability findings, 1 maintenance risk finding at or above medium (--fail-on medium).",
    );
  });

  it("returns null on a clean run so output is unchanged", () => {
    expect(
      failingGateSummary([{ label: "vulnerability", findings: [{ severity: "low" }] }], "high"),
    ).toBeNull();
  });

  it("returns null when --fail-on is not set", () => {
    expect(
      failingGateSummary([{ label: "vulnerability", findings: [{ severity: "critical" }] }], ""),
    ).toBeNull();
  });

  it("returns null for an empty class list", () => {
    expect(failingGateSummary([], "low")).toBeNull();
  });
});
