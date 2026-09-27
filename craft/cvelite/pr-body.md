Closes #1000.

The maintainer decision in the issue is option 1, document the scope, plus the gate line. This PR does both parts.

Part one is documentation. The `--only-used` and `--fail-on` entries in cli-reference.md now state that `--only-used` scopes vulnerability findings only, while override hygiene and maintenance risk findings gate independently. Neither is a reachability question, so filtering them would let the flag hide override misconfiguration.

Part two is the gate line. No `--fail-on` failure was explained in the output for any finding class. The maintainer's own reproduction shows the problem. Running

```
cve-lite examples/oa009-stale-floor --check-overrides --only-used --fail-on low
```

exits 1 with nothing in the output naming the gate, the threshold, or the class that tripped it. Grepping the whole output for "fail", "threshold", "gate" and "exceed" returns nothing.

The fix adds a `failingGateSummary` helper in `src/utils/severity.ts` next to `reachesFailOn`, since both read the same severity order. It takes the three finding classes the gate ORs, counts how many findings in each class meet or exceed the threshold, and returns one line in the format the issue requested.

```
Failing: 1 override hygiene finding at or above low (--fail-on low).
```

Both scan paths call it right after the `shouldFail` computation. `src/scan/single-scan.ts` skips the line in JSON mode and in fix mode, where the exit code is deliberately zero. `src/scan/multi-folder-scan.ts` skips it in JSON mode. A clean run, a run without `--fail-on`, or a run where nothing meets the threshold prints nothing, so existing output is unchanged.

Line references from the issue body are stale in the way the maintainer noted, so the patch anchors on the current locations. The gate lives at `src/scan/single-scan.ts` around line 657 and `src/scan/multi-folder-scan.ts` around line 453 after #1129.

Per the sequencing note in the issue, this touches neither `src/cli/args.ts` nor `src/overrides/context-builder.ts`, so it does not collide with #1228 or #1202.
