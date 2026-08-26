# Claims and Evidence

Read this reference before final scripting and again immediately before final
export.

## Claim Ledger

Classify every factual or numerical statement as one of:

- `fact`: directly supported by a current attributable source;
- `computation`: derived from recorded inputs with reproducible math;
- `benchmark`: measured under a locked protocol and bounded scope;
- `projection`: forward-looking estimate with assumptions and uncertainty;
- `opinion`: clearly framed judgment or creator perspective; or
- `blocked`: unsupported, private, stale, unverifiable, or not approved.

Record each claim in a ledger with:

| Field | Requirement |
| --- | --- |
| Claim ID and text | Stable ID and proposed spoken or visible wording |
| Type | Fact, computation, benchmark, projection, opinion, or blocked |
| Source or raw evidence | Source ID, inputs, capture, or benchmark artifact |
| Public-safe status | Approved, caveated, blocked, or needs authority |
| Allowed wording | Strongest wording the evidence actually supports |
| Caveat and scope | Conditions, population, project, version, and exclusions |
| Freshness deadline | Recheck time or documented stable-source rationale |
| Planned proof | Exact screenshot, footage, table, terminal log, or graphic |
| Readiness | Ready, stale, blocked, or awaiting evidence |

Blocked claims cannot ship as verified facts. A projection or opinion cannot
be restyled as an observed result. Reverify a claim that can change daily
within 24 hours of final export, and recheck any source whose deadline expires
before delivery.

## Honest Evidence Routes

Choose the smallest route that proves the claim:

- Explanation: official documentation, attributable source capture, real
  product footage, or a clearly labeled diagram.
- Demonstration: capture the actual behavior and the state needed to reproduce
  it.
- Computation: preserve source values, formula, units, and reproducible output.
- Benchmark or case study: use the locked protocol below.

Real site footage can demonstrate visual or behavioral continuity. It is not
exact version proof unless the footage or adjacent evidence actually
establishes the version. Never fabricate terminal output, use stock footage as
product proof, hide a material caveat, or convert a project-specific result
into a universal claim.

## Benchmark Protocol

Benchmarks are optional and run only when a benchmark claim is approved. Lock
the protocol before measuring:

- source repository, immutable commit or archive, and project-specific scope;
- machine and relevant hardware, OS, runtime, package manager, lockfile, and
  dependency versions;
- routes, fixtures, commands, build mode, environment shape, and configuration
  while excluding secrets;
- baseline and candidate definitions, cache state, warmups, measured runs, and
  run order;
- statistic, sample count, units, range or dispersion, failures, and outlier
  policy; and
- raw logs, timestamps, result files, source hashes, and a benchmark manifest.

Keep source, machine, routes, commands, runtime, package manager, and
environment constant between baseline and candidate unless the changed factor
is the explicit subject of the benchmark. Report statistics and ranges, not a
single favorable run. Preserve raw logs and the manifest privately; publish
only artifacts and wording approved as public-safe.

## Evidence Approval Gate

The final script is blocked until every planned claim is ready, caveated, or
removed; every proof maps to a source or raw artifact; daily-changing claims
have a valid freshness window; and the public-safe wording is explicit.
