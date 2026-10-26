# LegacyBench pilot protocol (v0, $200)

This is the operational companion to section 9 of the design brief. `prereg/PREREG.md`
is the registered text; this document explains the choices.

## Why a pilot and not a benchmark

A frontier agentic repository task costs roughly $2 to $5 on Claude Fable 5.1 and
$0.50 to $1.50 on the $2 / $10 models. Two hundred dollars is about 150 to 200
trajectories across four models at one run per task. At 50 tasks per model and k = 1,
the minimum detectable difference between two models is 25 to 30 percentage points.
Anything smaller is noise. So the pilot's job is to produce four things that are
true at this scale:

1. Each model's measured output ceiling (one call per length is enough).
2. A harness that a funded study can run unchanged.
3. Measured per-task cost, time and score variance, which turn the power table in the
   brief into a budget request.
4. A descriptive first look at single-shot versus agentic migration, labelled exploratory.

## Tasks

Sixteen Java 8 Maven repositories from FreshBrew (arXiv 2510.04852), chosen by size
stratum among single-module repos with at least ten tests run. `tasks/pilot.yaml` is
generated from FreshBrew's data by `scripts/build_pilot_manifest.py`, so the
selection is reproducible.

| Stratum | Repos | LOC | Estimated full-emission output | Arms |
|---|---|---|---|---|
| S | AdRoll/cantor, JakeWharton/DiskLruCache | ~1,150 to 1,220 | ~12K to 13K tokens | single-shot, agentic |
| M | vincentrussell/sql-to-mongo-db-query-converter, square/javapoet | ~5,050 to 5,100 | ~50K tokens | single-shot, agentic |
| L | perwendel/spark, julienchastang/charts4j | ~13,950 to 15,100 | ~140K to 150K tokens, above a 128K cap | single-shot, agentic |
| B | kafka-spout, Surus, caesar, ReloadablePropertiesAnnotation, mongobee, rsql-parser, patricia-trie, spring-context-support, dynamodb-streams-kinesis-adapter, HiveRunner | ~1,000 to 5,300 | n/a | agentic |

The estimate uses ten tokens per Java line, an assumption the single-shot arm will
replace with a measurement. javapoet and spark are famous repositories; the pilot does
not assess contamination and says so.

## Oracle

MigrationBench gates (arXiv 2505.09569) plus FreshBrew's coverage guard, evaluated
inside the sandbox against a read-only reference copy of each repository:

1. `mvn compile` succeeds on JDK 17.
2. `mvn test` succeeds; all original tests pass.
3. Every file under `src/test` is byte-for-byte identical to the reference.
4. Tests run is not lower than the baseline recorded in the manifest.
5. Every compiled class has major version 61 or higher.
6. Line coverage after, divided by coverage before, minus one, is greater than -0.05.
   This is FreshBrew's rule and it is relative, not percentage points.

A task passes only if every gate passes. Per-gate results are kept so failures are
attributable.

## Arms

Single-shot: the model receives every source and build file and must return the
whole migrated repository in one response in a fenced multi-file format, no tools.
Truncation, stop reason, output and reasoning tokens are recorded. This arm is
handicapped by output caps on purpose; that is the measurement.

Agentic: one minimal scaffold for all models, Inspect's basic ReAct agent with a shell
and a file editor, running as a non-root user in a sandbox with no network, JDK 8 and
17, and an offline Maven cache. Same system prompt for every model.

## Budget

| Item | Design | Estimate |
|---|---|---|
| Output-ceiling probe | 4 lengths x 4 models, one retry rule | ~$25 |
| Single-shot arm | 6 tasks x 4 models | ~$55 |
| Agentic arm | 6 tasks x 4 models, caps $5 Fable / $1.50 others | ~$55 |
| Breadth sample | 10 tasks x 3 models (no Astra), agentic | ~$35 |
| Reserve | retries, harness mistakes | ~$30 |
| Total | | ~$200 |

Compute is free: a public repository's GitHub Actions runners (4 vCPU, 16 GB, Docker,
six-hour jobs) or a laptop. Prices are frozen in `legacybench/prices.yaml`; the Astra
entry is blank and the ledger refuses to run a model without a complete entry.

## Order of operations

1. Fill and re-verify `prices.yaml` on the vendor pages. Decide effort settings.
2. Freeze: `bash prereg/hash.sh`. Push the tag.
3. Probe each model. Record measured caps in the report, not in the registration.
4. Build the sandbox image and run `scripts/verify_image.py`. Every manifest repo must
   build and pass its tests on JDK 8 inside the image; a repo that does not is removed
   and the removal is logged as a deviation.
5. Run the single-shot arm, then the agentic arm, one model at a time, interleaving
   models by day where possible.
6. Produce the ledger and descriptive report.
7. Write the plain-language note, first paragraph stating what the pilot cannot claim.

## Known shortcuts the full study must not take

Single annotator. One run per task. Public tasks only. No COBOL. No human baselines.
No external replication, though the released harness makes one possible for anyone
with their own $200. Two of the kept benchmarks (RepoTransBench, RepoMod-Bench) and
all of CRUST-Bench and SWE Refactor Bench are deferred.
