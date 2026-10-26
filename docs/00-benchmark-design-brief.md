# LegacyBench v0 design brief: what a top benchmark scientist would do, and the brief to execute

Status: complete. Four research passes (benchmark design science, evaluation statistics, audit of the six named benchmarks with repos cloned and inspected, modernization domain plus model pricing) are digested in Appendices A to D. Sections 0 to 6 are the answer; section 0 makes the LinkedIn thesis falsifiable and section 5 is the rewritten prompt.

## Context

The request: build an aggregate "Legacy Modernization" benchmark from six existing mini-benchmarks, run three frontier models at high effort, measure quality / cost / time, aggregate with sound statistics, publish at journal quality in plain language. The meta-request: before rewriting that prompt, establish from primary sources what a top professional would do that is not being asked for, what raw material they would start from, what methods and tools they would use, and what external evidence would show the result is right. A follow-up asked whether the six are even the right benchmarks.

Repository `kelapure/legacybench` is empty (no commits). Nothing to reuse. The LinkedIn post was pasted in by the user; its thesis is that Gemini 4 Argon's 1M-token decode window makes it the best model for legacy modernization because it can emit a whole modernized microservice plus tests in one response. Section 0 turns that thesis into registered hypotheses. The replies were not provided.

**Short answer on the six**: four should be dropped and two kept with fixes. LongWriter and HelloBench are prose benchmarks with LLM judges (LongWriter's judge is pinned to a GPT-4o snapshot now scheduled for retirement). Commit0 asks models to regenerate flask, requests and pydantic from spec, which rewards memorisation, and its maintainers have already patched reward hacking. REPOCOD is single-language function completion on scikit-learn and sympy. RepoTransBench is on-construct but its LLM-generated tests are writable by the agent (open issue, Aug 2026) and its headline subset is unclear. RepoMod-Bench is on-construct and the only large-repo set, but is vendor-run, scores CLI agent products rather than models, and includes tasks whose target-language ports already exist (jq to gojq, httpie to xh). The 2025-2026 literature now has directly on-construct, execution-verified alternatives: MigrationBench, FreshBrew, CRUST-Bench, SWE Refactor Bench. A COBOL/mainframe axis of acceptable quality does not exist and would have to be built.

## 0. The thesis behind the six benchmarks, made falsifiable

The LinkedIn post argues four things. (1) Fable 5.1 and GPT-6 Astra cap standard output at 128K tokens (Fable 300K in a Batch API beta), and reasoning tokens consume that budget, so 50K tokens of thinking leave about 78K for code. (2) Argon's 1M decode window lets a model reason for 200K tokens and still emit 500K tokens, roughly 35,000 to 50,000 lines, of code. (3) Emitting a whole modernized microservice, API routes, data models and characterization tests in one atomic response keeps type definitions and dependency injection consistent from the first file to the fiftieth. (4) Therefore Argon is the best model for legacy modernization. LongWriter and HelloBench were in the list to stand in for "output ceiling" and "quality degradation with length".

This is a legitimate construct measured with the wrong instrument. Output budget, the reasoning-versus-code split, and cross-file consistency are real, measurable properties that decide whether one-shot generation is viable. Prose benchmarks measure none of them on code. The post is also a set of empirical claims, and a benchmark built around it must be able to refute each one:

- **Claim A, ceilings.** The research found conflicting figures: Argon default max output 65,536, "long decode" up to 1M, and one API probe returning 32,768; Fable 128K synchronous; Sol 128K. Whether thinking tokens count against each cap differs by vendor. These must be measured by probe, not quoted from marketing or docs.
- **Claim B, one shot beats iteration.** The counter-hypothesis from the agentic-benchmark literature is that iterative generation with compile and test feedback wins at matched cost, and that single-shot defect rate rises with output position, which is HelloBench's degradation finding transferred to code. This is the central test.
- **Claim C, consistency.** "100% consistent" is a measurable number: unresolved symbols and type errors per cross-file reference after compilation, single-shot arm versus agentic arm.
- **Claim D, best for modernization.** A ranking claim across the whole construct, not one-shot translation alone. It is exactly what the pre-registered primary comparison in section 5 tests, and with three models and six-plus sub-benchmarks it will most often come back "underpowered" rather than confirmed or refuted; the brief says so in advance.

Design consequences, carried into section 5: a long-output code axis with tasks stratified by target output size; a single-response arm and an agentic arm for every model at matched dollars and matched wall-clock; an output-ceiling probe before pre-registration; hypotheses H1 to H3 registered with a ROPE; the reasoning-versus-code token split, truncation rate and decode speed reported per model. Fable's 128K cap means it cannot emit a 500K-token artifact in one response; that is the thesis under test, not a flaw in the design, and the headline arm lets each model use its best registered mode. Two cautions: a 500K-token response at observed decode speeds may take over an hour, so wall-clock is a first-class axis here, not a footnote; and the post compares Argon to GPT-6 Astra while this plan evaluates GPT-6.1 Sol, so either Astra is added as a fourth model or the substitution is stated.

The post's metaphor, an architect who can read a thousand-page blueprint but write only two pages before forgetting, is good material for the plain-language report if the data support it. If iteration wins, the honest version is that architects also work in drafts.

## 1. What a top professional would do that the prompt does not ask for

The prompt asks for a bundle, a run, an aggregate and a write-up. A top evaluation scientist (the people behind SWE-bench Verified, HAL, METR's task suites, HELM and LiveCodeBench) would do eleven things the prompt skips. Each is anchored in Appendices A to C.

1. **Define the construct before choosing tests.** Write down what "legacy modernization" is, decompose it into capabilities (comprehend old code; translate across languages with behavior preservation; upgrade language version, framework and dependencies in place; write characterization tests where none exist; sustain repo-scale agentic work), declare what is out of scope, and only then pick a test per capability. The current six were chosen because they exist. Two (LongWriter, HelloBench) are prose benchmarks with LLM judges; two (Commit0, REPOCOD) are from-scratch and function-completion tasks on popular, memorized Python libraries; the two on-construct ones (RepoTransBench, RepoMod-Bench) have agent-writable tests and existing-port contamination respectively (Appendix D). Raji et al. 2021 and Dehghani et al. 2021 name this failure: an aggregate of convenient tasks has no construct, and rankings change with task selection.

2. **Re-validate every inherited task; do not trust by citation.** SWE-bench Verified exists because ~one third of original tasks were underspecified or had unfair tests, and even Verified later lost a 59% flawed hard tail (OpenAI, Feb 2026). Apply the same rubric here: a 0-3 severity rating by three independent annotators on (a) underspecification and (b) tests rejecting correct solutions, discard 2-3, publish the annotations.

3. **Decontaminate by date and probe memorization.** Every candidate benchmark except RepoMod-Bench (Feb 2026) and the 2026 modernization benchmarks predates the three models' training. The professional move is a two-tier benchmark: a frozen public split plus a post-cutoff split built from migrations committed after the models' cutoffs (LiveCodeBench, SWE-rebench, K Prize pattern), with the SWE-Bench Illusion file-localization probe and Golchin-Surdeanu guided completion run on every model.

4. **Use execution oracles independent of any LLM, and measure oracle strength.** Test pass rate is only as good as the tests. Report mutation score of each task's test suite (PIT, Stryker, mutmut), coverage-preservation (FreshBrew's <= 5 pp rule to catch test deletion), differential testing against the original system (Diffy pattern, sudo-rs `SUDO_UNDER_TEST` pattern), and byte-identical output for batch programs. Where an LLM judge is unavoidable, use a cross-family judge, swap order, and report Krippendorff's alpha against humans.

5. **Hold effort and scaffold constant, and treat both as variables.** "High effort" is the default for Fable 5.1, one notch above default for Argon and Sol, and Fable exposes xhigh and max above it. METR showed scaffold choice flips rankings; HAL found higher effort reduced accuracy in a majority of runs. Run one shared minimal scaffold (Inspect solver) for the headline, plus each vendor's first-party agent as a secondary arm, and report effort sweeps for at least one benchmark.

6. **Human baselines.** METR's HCAST protocol: qualified engineers attempt a stratified sample of tasks under agent-identical conditions, so scores read as "fraction of what a competent engineer does" rather than an abstract percentage. Without this the plain-language story has no anchor.

7. **Cost-controlled reporting.** Kapoor et al. 2024 and HAL: pair every accuracy with dollars and tokens, plot the Pareto frontier with bootstrap bands, log the frozen price sheet and date, and include a trivial retry baseline that cheap agents must beat.

8. **Pre-register the analysis.** Hypotheses, primary metric per benchmark, k runs, exclusion rules, normalisation, ROPE, correction family, aggregation hierarchy, all hashed in a git tag or on OSF before the first API call. Otherwise the choice of normalisation is a forking path that can pick the winner.

9. **Power the study honestly.** With 3 models and 6 benchmarks, Friedman and Wilcoxon can only detect unanimous dominance. A 50-task sub-benchmark with 3 runs detects ~18-point gaps. State the minimum detectable effect per benchmark up front and label results "underpowered" rather than "no difference" when the interval admits the smallest effect of interest.

10. **Failure taxonomy over leaderboard.** Classify every failed trajectory into Pan et al.'s 15 translation bug categories (extended for upgrades and tests), plus METR's spurious / tradeoff / real split. With three models the taxonomy is the durable scientific contribution; the ranking will be obsolete in a quarter.

11. **Release like a dataset paper and disclose conflicts.** Datasheet, Croissant metadata, license, hosting and maintenance plan, errata channel, replication script, encrypted trajectories with a training-exclusion request (NeurIPS D&B bar, BetterBench). Declare 8090.ai's commercial interest in modernization and any vendor relationships, and invite an independent re-run before publication.

## 2. The rawest material they would start from

Not the six benchmarks. The rawest ground truth for modernization is **a human-performed migration in public git history, with the original and the target both under test, and the tests written by people, not models.** Each of these gives an oracle no LLM produced:

- **Historical commits**: SciPy's Fortran-removal PRs (Fortran to C/Cython under the full SciPy suite); Python 2 to 3 migrations in the PyComply corpus projects; JUnit 3/4 to 5, javax to jakarta, Joda to java.time changes in Apache/Eclipse projects; MigrationBench's 5,102 Java 8 Maven repos with existing tests.
- **Paired implementations with shared suites**: uutils/coreutils (GNU coreutils C and its test suite, 645/690 passing against the Rust port), sudo-rs (compliance suite switchable between original and port), zlib-rs against zlib-ng's byte-exact stream tests, LAPACK's reference drivers for Fortran ports.
- **Mainframe**: AWS CardDemo (COBOL/CICS/BMS/VSAM/JCL, Apache-2.0; oracle = batch output datasets and screens) and the NIST COBOL85 suite via GnuCOBOL (~9,688 tests) as an executable COBOL semantics oracle.
- **Practitioner validation data**: AWS Transform's dataset-comparison equivalence reports, IBM's symbolic-execution-generated JUnit tests for COBOL to Java (arXiv 2504.10548), Google's 39-migration FSE 2025 study with edit-level authorship data.
- **Failure data**: the 1,748 labelled failed translations from Pan et al. (ICSE 2024 artifact) as the seed taxonomy.

The digested substitutes (the six benchmarks) are second-order: they are someone else's selection of repos, with tests sometimes LLM-assisted, and public since 2024.

## 3. Specific methods and tools

- **Harness**: UK AISI Inspect (dataset / solver / scorer separation, per-sample Docker sandbox with `network_mode: none`, token / time / cost limits, `.eval` logs with full transcripts and raw API records). METR retired its own Task Standard in favour of Inspect. HAL harness conventions for cost logging and encrypted trace upload.
- **Task validation**: SWE-bench Verified rubric (0-3 on underspecification and unfair tests, three annotators); SWE-ABS / UTBoost style test strengthening; FreshBrew coverage-preservation; mutation score via PIT, Stryker, mutmut, cosmic-ray; errata file.
- **Equivalence oracles**: differential testing (Diffy with a secondary instance to measure nondeterminism, GoReplay), Hypothesis Ghostwriter `--equivalent` and jqwik for property-based equivalence, byte-identical batch output, SymDiff / RustAssure / Kani for bounded formal equivalence where feasible.
- **Contamination**: date-segmented splits (LiveCodeBench, SWE-rebench), SWE-Bench Illusion file-localization probe, Golchin-Surdeanu guided completion, Oren et al. permutation test where log-probs and a canonical order exist.
- **Statistics**: Miller's clustered and paired estimators (`errorbars`), Wilson or Beta-Binomial intervals for small n (Bowyer et al. 2025), rliable IQM and stratified bootstrap and probability of improvement, Chen pass@k and tau-bench pass^k estimators, Holm correction, baycomp Bayesian signed-rank with ROPE, MCB confidence set for "best model", BCa bootstrap for cost, Pareto frontier with bands.
- **Judging where unavoidable**: cross-family judge, order swap, human sample with Krippendorff's alpha >= 0.80 target.
- **Elicitation**: METR elicitation guidelines (minimal scaffold, shell with visible output, context management), spurious / tradeoff / real failure classification, effort sweep.
- **Release**: Datasheets for Datasets, Croissant metadata, CC-BY-4.0 data and permissive code license, versioned splits, OSF pre-registration, replication script.

## 4. What, other than you or me, would show the result is right

1. **Pre-registered predictions that come true or fail in public.** The analysis plan, hypotheses and minimum detectable effects are hashed before the first run. Deviations are listed. A reader can check that the reported analysis is the registered one.
2. **An independent re-run.** A third party (Vals, Epoch, HAL, or a university group) reproduces the headline numbers from the released harness and task set within the reported confidence intervals. Offer encrypted trajectories and the Docker images; the replication script is part of the release.
3. **Oracle strength numbers.** Mutation scores and coverage-preservation per task are published; reviewers can see that passing tests means something. Where differential testing against the original system exists, the fraction of outputs matching byte-for-byte is reported.
4. **Human baselines.** A stratified sample of tasks has qualified-engineer completion times and success rates under the same conditions, so model scores are anchored to something outside the model world.
5. **Contamination evidence.** Scores on the post-cutoff split, the file-localization probe, and the guided-completion probe are reported per model. A public-split score that collapses on the fresh split is reported as such.
6. **Human-validated judging and tasks.** Annotator agreement (Krippendorff's alpha with CIs) on task validity and on any judge-scored item is published, with the annotations.
7. **Convergent validity with other independent measurements.** The ranking and effect sizes are compared against independent modernization results that already exist (SWE Refactor Bench, FreshBrew, MigrationBench, Vals Terminal-Bench 4.0, TRACTOR). Agreement is evidence; disagreement is explained, not hidden.
8. **Adversarial review before publication.** Frontier-lab evaluators and the authors of the component benchmarks are sent the draft and the task set with an invitation to break it; their findings and the fixes are in the paper.
9. **Statistical honesty checks a reader can perform.** Every claim carries a CI; the "underpowered" label appears where it should; Holm-adjusted p-values and the full set of tests performed are tabulated.
10. **Ongoing falsifiability.** Monthly fresh-task additions and an errata channel mean later submissions and later models test whether the benchmark still discriminates.

## 5. Rewritten prompt

Hand this to the executing team or agent verbatim. Bracketed items are parameters to set.

---

**Build LegacyBench v0: a pre-registered, execution-verified benchmark of frontier models on legacy software modernization, with an independent replication and a plain-language report.**

Models: Claude Fable 5.1 (`claude-fable-5-1`), Gemini 4 Argon (`gemini-4-argon`), GPT-6.1 Sol (`gpt-6.1-sol`). Budget ceiling: [$X] API spend, [$Y] human annotation and baselining, [Z] weeks. Work in phases with a gate at the end of each; do not start API runs before Gate 4.

**Phase 0. Construct memo (gate: one page, reviewed by two people who have shipped a modernization).**
Define legacy modernization operationally and decompose it into five capabilities: (a) comprehension of large undocumented code, (b) cross-language translation with behavior preservation, (c) in-place language, framework and dependency upgrade, (d) characterization-test generation for untested code, (e) sustained repo-scale agentic work. Declare non-goals (greenfield generation, prose, UI redesign, data migration). Every sub-benchmark must map to one capability and state its primary metric, floor and ceiling.

**Phase 1. Benchmark selection and task validation (gate: validated task manifest with annotations published).**
Do not inherit any task by citation. Start from this slate and justify every inclusion and exclusion in a selection memo:
- Capability (c): MigrationBench selected-300 and FreshBrew (Java 8 to 17/21). Keep FreshBrew's coverage-within-5-pp rule and MigrationBench's test-methods-unchanged rule for both.
- Capability (b): RepoTransBench v2 on a fixed, published, per-pair stratified subset with test suites made read-only and hash-verified; CRUST-Bench (C to safe Rust); RepoMod-Bench with tasks flagged where a target-language port already exists publicly (jq to gojq, httpie to xh, check all 21), weighted by task not by test, run through the neutral scaffold in Phase 2; SWE Refactor Bench if its license and harness check out, adopting its migration-audit stage everywhere.
- Capability (d): build a characterization-test task set from the same repos: strip tests from a module, ask for tests, score by mutation score of the generated suite against the original implementation (PIT / Stryker / mutmut), require all generated tests to pass on the original.
- Capability (a) and the legacy-stack gap: build [N, target 30 to 50] COBOL/CICS tasks from AWS CardDemo (Apache-2.0) with batch output datasets as the oracle, plus NIST COBOL85 semantics tests via GnuCOBOL as a translation oracle. If this cannot be done within budget, declare the gap explicitly rather than substituting COBOLEval or MainframeBench.
- Fresh split for capability (b) and (c): mine human-performed migration commits dated after each model's training cutoff (SciPy Fortran removal, Python 2 to 3 projects, JUnit and jakarta migrations, uutils/coreutils, sudo-rs, zlib-rs) and freeze a dated post-cutoff split; plan monthly additions.
- Exclude LongWriter, HelloBench, Commit0 and REPOCOD from scoring. Replace the long-output construct the first two stood in for with a direct code measure, the **long-output code axis**: select translation and migration tasks stratified by required target size (about 20K, 50K, 100K, 250K and 500K tokens of code plus tests). Run every model in a single-response, no-tools arm (source, schemas and spec in; the whole target repository out as files in one response) and in the agentic arm. Score both by build, tests, mutation score, cross-file consistency (unresolved symbols and type errors per cross-file reference), truncation rate, reasoning-versus-code token split, decode tokens per second, and defect rate by output position. Compare arms at matched dollars and at matched wall-clock. This is the test of the one-shot thesis in section 0.
- Controls: a trivial retry baseline (Kapoor et al. 2024) and, if budget allows, SWE-rebench's latest monthly split as a general-coding reference.
For every task: three independent annotators rate 0-3 on underspecification and on tests rejecting correct solutions (SWE-bench Verified rubric); discard ratings of 2-3; publish annotations and Krippendorff's alpha. Report mutation score and coverage of every task's oracle. Strengthen weak suites (SWE-ABS / UTBoost pattern) and record the before/after. Keep an ERRATA file.

**Phase 2. Harness (gate: one end-to-end run of one task per sub-benchmark per model, logs inspected by hand).**
Use UK AISI Inspect: dataset / solver / scorer separation, per-sample Docker sandbox with no network, token, time and cost limits, `.eval` logs with full transcripts and raw API records. One shared minimal scaffold for the headline arm (METR elicitation guidelines). Vendor first-party agents as a secondary arm only. Pin prompts, task versions and commit hashes. Record per call: input, output, cached and reasoning tokens, wall-clock split into model latency, queue or rate-limit wait and tool execution, provider, region, timestamp, concurrency. Interleave models in time. Compute dollars as a pure function of tokens and a dated frozen price sheet (as of today: Fable $10 / $50, Argon $2 / $10 rising to $4 / $20 on 2026-12-01, Sol $2 / $10; re-verify Google and OpenAI pages before freezing). Before Phase 3, run an **output-ceiling probe** per model at the registered effort with thinking on: request a checkable artifact of known length (for example, a generated corpus of 600K tokens of code that must compile), and record the actual truncation point, whether thinking tokens count against the cap, decode tokens per second, any long-decode flag or batch mode required, and the behavior at the cap (hard stop, `max_tokens` finish reason, or silent truncation). Documentation disagrees today (Argon 65,536 default and 1M long decode but one probe returned 32,768; Fable 128K synchronous and a claimed 300K batch beta; Sol 128K). The measured values, not the documented ones, go into the pre-registration.

**Phase 3. Pilot and cost calibration (gate: measured per-task token and time distributions).**
Run [5] tasks per sub-benchmark per model at the chosen effort. Replace all cost estimates with measured medians and p95s. Decide k runs per task from the power formula in Phase 4 and the budget; k must be equal for all models.

**Phase 4. Pre-registration (gate: SHA-256-hashed git tag or OSF registration before any scored run).**
Register: hypotheses, including the three from section 0, H1: single-response generation does not beat agentic generation on behavior-preserving success at matched cost (ROPE 2 pass-rate points); H2: cross-file consistency of single-response output does not exceed agentic output by more than [x] percentage points of cross-file references; H3: the measured output ceiling predicts success only on tasks whose target exceeds the smaller models' caps, and not elsewhere; primary metric, floor, ceiling and ROPE (smallest effect of interest, e.g. 2 pass-rate points) per sub-benchmark; k; cluster definition (repo or task family); exclusion rules for timeouts and infrastructure failures; effort setting per model and the parity rationale (high is Fable's default but one notch above default for Argon and Sol; Fable also has xhigh and max); the full aggregation hierarchy: primary = per-benchmark paired differences on the primary metric (forest plot), secondary = Borda / mean rank, normalised IQM with stratified bootstrap and probability of improvement, Bayesian signed-rank with ROPE; Holm correction over the 18 primary tests per metric, Benjamini-Hochberg for exploratory metrics; minimum detectable effect per sub-benchmark at k; judge-validation threshold (alpha >= 0.80) where any judge is used. List deviations in the final report.

**Phase 5. Scored runs.** k runs per task, all models, headline scaffold; effort sweep (low / default / high / max where available) on at least one sub-benchmark; secondary vendor-agent arm if budgeted. Encrypt and archive all trajectories.

**Phase 6. Analysis.** Follow the registered plan exactly: clustered and paired estimators (Miller 2024), Wilson or Beta-Binomial intervals where n < 200, Chen pass@k and tau-bench pass^k with task-level bootstrap, rliable IQM and performance profiles, baycomp signed-rank with ROPE, MCB confidence set for "best model", BCa bootstrap on cost, Pareto frontier of accuracy vs dollars with bands, p50 / p95 latency with rate-limit time separated. Label every underpowered comparison "underpowered", not "no difference". Publish the full table of tests performed.

**Phase 7. Failure taxonomy and human baselines.** Label every failed trajectory using Pan et al.'s 15 translation bug categories, extended for upgrade and test-generation failures, plus METR's spurious / tradeoff / real split; two labellers, report alpha. Run METR-style human baselines on a stratified [30-task] sample with qualified engineers under agent-identical conditions, recording time and success, including failures.

**Phase 8. Contamination and external validation.** Report per model: scores on the frozen public split vs the post-cutoff split; SWE-Bench Illusion file-localization probe; Golchin-Surdeanu guided completion. Compare effect sizes and rankings with independent results (SWE Refactor Bench, FreshBrew, MigrationBench, Vals Terminal-Bench 4.0, TRACTOR) and explain disagreements. Send the task set and draft to at least two external evaluators (frontier-lab eval teams, component-benchmark authors, Vals / Epoch / HAL) with an invitation to break it; incorporate findings. Commission or arrange one independent re-run of the headline numbers from the released harness.

**Phase 9. Release and report.** Release under CC-BY-4.0 data and a permissive code license with a datasheet, Croissant metadata, versioned splits, replication script, errata channel, maintenance plan and a training-exclusion request. Write two documents: (1) a technical report at NeurIPS Datasets & Benchmarks standard, with a conflict-of-interest statement covering 8090.ai's commercial position and any vendor relationships; (2) a plain-language report a high-school reader can follow, where every claim is traceable to a figure with a confidence interval, and every "we don't know" is stated.

**Sub-agent decomposition.** Run in parallel where independent: (1) task curation and annotation per sub-benchmark, (2) harness and sandboxing, (3) oracle-strength tooling (mutation, coverage, differential), (4) COBOL task construction, (5) fresh-split mining, (6) statistics and pre-registration, (7) failure-taxonomy labelling, (8) external review coordination, (9) writing. One integrator owns the manifest and the registered plan; no agent may change a registered parameter.

**Acceptance criteria.** Every scored number has a CI and a sample size. Every task has an annotation record and an oracle-strength score. The registered plan hash matches the analysis. The post-cutoff split is reported. At least one independent party has reproduced the headline table. The plain-language report has been read back by someone outside the project who could restate the main finding and its uncertainty correctly.

---

## Cost envelope (estimates, assume a factor of 2 either way; replace with Phase 3 measurements)

| Item | Assumption | Estimate |
|---|---|---|
| API, headline arm, one pass, all models | MigrationBench-300, FreshBrew-100, RepoTransBench-130, CRUST-100, RepoMod-21, char-test-100, COBOL-40; agentic runs 150K-500K tokens per task, mostly cached input; Fable ~3-5x the other two per token | ~$12-20k per pass (Fable ~$9-14k, Argon and Sol ~$2-3k each) |
| API, k = 3 passes | | ~$35-60k |
| Effort sweep on one sub-benchmark + vendor-agent arm | | +$15-30k |
| Pilot | 5 tasks x 7 sub-benchmarks x 3 models | ~$1-2k |
| Task validation | 3 annotators x ~800 tasks x ~15 min at ~$75/h | ~$45k |
| Human baselines | 30 tasks x 2 baseliners x ~4 h at ~$150/h | ~$36k |
| COBOL task construction | 40 tasks, ~1 engineer-month | ~$20-30k |
| Compute for Docker test execution, mutation runs | | ~$3-6k |
| Independent re-run | API costs for one pass by a third party, in-kind labour | ~$15-20k |
| **Total, credible v0** | | **~$170-250k** |
| **Lean v0** | k = 3, no vendor arm, annotation on a 300-task sample, no human baselines, COBOL declared as a gap | **~$70-100k** |

Argon's price doubles on 2026-12-01; Sol's current price is reportedly promotional through 2026-11-21. Freeze the price sheet and report tokens so the result survives price changes.

## 6. Open questions and assumptions

Assumptions made in the rewritten prompt, to be confirmed or overridden:
1. **Scoring excludes the four off-construct benchmarks.** Alternative: run them once, label them "not modernization", and report them in an appendix as diagnostics. The rewritten prompt excludes them.
2. **COBOL axis is built, not borrowed.** This is the single largest schedule and cost risk. The prompt allows declaring it a gap; the choice is the user's.
3. **Effort parity.** "High" is Fable's default and above default for the other two. The prompt treats effort as a registered variable with one sweep; the headline setting needs a decision (each vendor's default, or "high" for all, or max available for all).
4. **Headline scaffold is neutral (Inspect), vendor agents secondary.** Reversing this measures products, not models.
5. **Budget ceiling and timeline** are unknown; the lean and credible envelopes bracket the decision.
6. **Independent replicator** is unnamed. Candidates: Vals, Epoch, HAL (Princeton), a university SE group.
7. **Venue**: NeurIPS Datasets & Benchmarks standard assumed; arXiv plus report is the fallback.
8. **Model set.** The LinkedIn post compares Argon to GPT-6 Astra; this plan evaluates GPT-6.1 Sol. Add Astra as a fourth model (roughly one third more API spend) or state the substitution in the report. The post's replies were not provided; if they contain objections, they belong in section 0.
9. **Prices for Argon and Sol** are medium confidence (aggregators, vendor pages unreachable from this sandbox); re-verify before freezing.

## 7. Verification of this plan

This is a research and writing deliverable, not code. Verification is by reading: each claim in sections 1 to 5 traces to a cited item in Appendices A to D; every item the research agents could not verify is marked in the appendices and carried into section 6. The rewritten prompt's acceptance criteria are the end-to-end test of the eventual work.

## Appendix D. Research notes: audit of the six named benchmarks (repos cloned and inspected read-only; papers via snippets; RepoTransBench manuscript read from its in-repo PDF)

| Benchmark | What it is | Oracle | Contamination / staleness | SOTA, saturation | Harness state | Modernization relevance | Verdict |
|---|---|---|---|---|---|---|---|
| LongWriter / LongBench-Write (THUDM, Aug 2024, Apache-2.0) | 120 essay prompts (60 zh / 60 en), 7 genres; required lengths 100-20,000 words, median 1,550 | Length score (piecewise linear) + quality 1-5 by GPT-4o `gpt-4o-2024-05-13` hard-coded, six dimensions, no references, no humans | Prompts public; same group trained LongWriter-6k / LongWriter-Zero toward it; judge snapshot scheduled for OpenAI shutdown 2026-10-23 (unverified), so canonical quality score may be unreproducible; arXiv 2606.04095 reports high scores partly from verbatim duplication the judge does not penalise | GPT-4o quality 91.8, Claude 3.5 Sonnet 87.7: quality axis at ceiling; length is the only discriminator and 128K-output models close it | pred.py / eval_quality.py, no Docker, API models by editing script; last commit 2025-06-24, 30 open issues | None (prose) | DROP |
| HelloBench (Sep 2024, MIT) | 647 prose tasks (open QA, chat, heuristic text gen, summarization, completion) + length-constrained variants | HelloEval: unpinned `gpt-4o` answers 4-6 checklist items per subcategory; weights from a regression fitted to 2024 human scores | Web-sourced texts; no refresh; checklist evaluation itself contested (arXiv 2508.15218) | No maintained leaderboard; no 2025-26 frontier scores | Last commit 2024-11-27, dormant | None (prose) | DROP |
| RepoTransBench (DeepSoftwareAnalytics, v1 Dec 2024, v2 Dec 2025, TSE 2026, MIT) | v2: 1,897 repo samples, 13 language pairs (C/C++/C#/Java/JS/Matlab/Python to Python/Java/Go/Rust/C#/C++); avg 23,966 tokens, 2,394 LOC per repo | Translated executable tests (avg line cov 81.9%), Success@1 = all tests pass; tests were generated and translated by an LLM multi-agent pipeline | GitHub repos > 50 stars, pre-2025, no decontamination; open issue Aug 2026: graded test suite is writable by the agent, mutations not detected | Claude Sonnet 4 / GPT-4.1 with authors' ReAct agent 32.8%; to-Python pairs 45-63%, to-static-languages < 10%; o3-mini C to Rust 67.2% | Docker Compose, authors' own ReAct loop, `run_batch` defaults to 5 projects per pair (65 of 1,897), unclear which subset headline covers; last commit 2025-11-09 | Direct (whole-repo translation with behavior preservation) but repos are small and modern, not legacy | KEEP WITH FIXES: make tests read-only and hash-verified, re-validate a sample of LLM-generated tests, fix and publish the subset, report per pair |
| Commit0 (Dec 2024, ICLR 2025, MIT) | Re-implement 16 (lite) / 54-57 (all; counts inconsistent) Python libraries (flask, requests, pydantic, networkx, statsmodels, web3.py) from spec + skeleton + tests | Original developer tests in Docker/Modal; % tests passed | The libraries are among the most-cloned Python packages; ground truth is verbatim in every pretraining corpus; agent sees tests; Feb 2026 commit "fix-reward-hacking-git-history" confirms exploitation; pass % dominated by huge suites (web3.py 40,433 tests) | OpenHands ~41-43% lite (Nov 2024); 56.2% with Opus 4.7 (2026); unsaturated but steep | pip-installable, Modal default, `agent` CLI supports aider only; last commit 2026-02-24 | Indirect at best: greenfield generation, nothing to preserve | DROP (or no-feedback setting with hidden tests, as a secondary generation axis) |
| REPOCOD (Purdue, Oct 2024, ACL 2025, BSD-3) | 980 whole-function completions in 11 Python repos (scikit-learn 314, sympy 97, astropy 85, ...), avg 313.5 tests per task | Developer tests in 11 Docker images, pass@1; authors publish `flaky_tests.json` | Targets are the actual upstream functions, canonical training data | GPT-4o + BM25 27.35, Claude 3.5 Sonnet 19.80 (2024); no 2025-26 model on leaderboard | Scripts + Docker; last commit 2025-08-27 | Weak: single-language repo-context completion | DROP |
| RepoMod-Bench / mcode-benchmark (Modelcode AI, arXiv 2602.22518, 26 Feb 2026, Apache-2.0 harness, GPL upstream sources included) | 21 repo-level translations, 8 languages, 14K to 211K LOC (1.6M total), 11,616 hidden tests; e.g. jq (C) to Go, httpie (Py) to Rust, hugo (Go) to Rust, prettier (JS) to Rust | Hidden pytest suites driving the binary / HTTP server externally so the same tests run on source and target; build success + pass rate; prompt forbids FFI/wrapping, "violations will be detected" but detector undocumented | Severe: real ports already exist in the target language (jq to gojq, httpie to xh), so memorised reproduction is indistinguishable from translation; per-task test counts 6 to 2,024 so pooled pass rate is dominated by a few repos | Claude Code + Opus 4.5 48.2%, Codex CLI 30.4%; 91.3% (< 10K LOC), 15.3% (> 50K LOC) | Docker Compose per task; agents are CLI products pinned in `agents.yml` (Claude Code, Codex, Gemini CLI, OpenCode), not bare models; REPRODUCE.md regenerates tables from author logs not in the repo; 5 stars, 1 issue; KDD '26 acceptance self-reported | Direct: the only one of the six whose construct is "port a large existing system and prove equivalence", though sources are modern OSS not legacy stacks | KEEP WITH FIXES: flag tasks with an existing target-language port (or similarity-check against it), weight by task, document the anti-cheat detector, run through a neutral scaffold, re-run rather than cite vendor numbers |

**Better-matched additions**
| Benchmark | Construct | Oracle | SOTA | Fit |
|---|---|---|---|---|
| MigrationBench (Amazon, May 2025, Apache-2.0; github.com/amazon-science/MigrationBench) | Java 8 to 17/21 repo migration; 5,102 full, 300 selected, 4,814 UTG | Build + original tests pass + class-file version + test methods unchanged + test count non-decreasing; maximal variant also requires deps at latest major | 62.3% minimal / 27.3% maximal (SD-Feedback, Claude 3.5); 71.7 / 53.3 with Strands + Sonnet 4.5 | Direct; accepts a diff or migrated dir from any agent |
| FreshBrew (Google et al., Oct 2025, NeurIPS 2025, Apache-2.0; github.com/mrcabbage972/freshbrew) | 228 repos that build on JDK 8 and fail on 17/21 | Compile + all original tests + coverage within 5 pp | Gemini 2.5 Flash 52.3% (v1), 56.5% (2026 revision) | Direct; coverage guard worth borrowing |
| CRUST-Bench (UT Austin / NYU, Apr 2025, COLM 2025, GPL-3.0) | 100 C repos to safe Rust against hand-written Rust interfaces and tests | Manual interfaces + tests | o3 19/100 single-shot | Direct, hard, unsaturated; no Docker, dormant since Apr 2025 |
| SWE Refactor Bench (Aug 2026, arXiv 2608.23564; license unverified) | 20 whole-repo stack migrations, 4 debt types | Migration audit + fixed behavioural tests + 6 independent verifier agents | 28/520 runs pass all three; best 47/100 | Direct and current; the audit stage catches "copy the old code and pass" |
| TransRepo-bench (Microsoft, Jan 2025) | 13 Java to C# repos, skeleton-guided | Fixed unit tests | not found | Direct, tiny, single pair |
| RustRepoTrans (Nov 2024) | 375 function tasks C/Java/Py to Rust with repo context | Tests | Claude 3.5 43.5% | Function granularity |
| T2J-Bench (May 2026) | 63 PyTorch to JAX repo migrations | Observational equivalence vs frozen references | best 0.676 | Direct (framework migration); unverified |
| Multi-SWE-bench / SWE-PolyBench / SWE-bench-Live / SWE-rebench | Multilingual issue resolution; the last two are monthly-refreshed | Tests | ~19% / 14.1% / Opus 4.6 65.3% (SWE-rebench, Mar 2026) | Indirect; control arm and the live-refresh template |
| COBOLEval (Bloop 2024, MIT), MainframeBench / XMainframe (FPT 2024), X-COBOL (2023), COBOL-JavaTrans (FPT, Apr 2026, release not found) | 146 HumanEval problems in COBOL; COBOL MCQ/QA/summarisation; 84-repo raw corpus; 143 COBOL-Java pairs | GnuCOBOL + ~6 tests; accuracy/BLEU; none; compile + pass@1 (vendor) | GPT-4o ~16.4 pass@1 on COBOLEval | COBOL axis at acceptable quality does not exist; must be built |

**Pan et al. "Lost in Translation" (ICSE 2024)**: 1,700 samples, 5 languages, 31 pairs, 6,197 attempts, 1,558 failures, 1,748 manually labelled bugs in 15 leaf categories across 5 groups: (1) syntactic/semantic differences between PLs, (2) changes in logic (added, missing, altered behaviour), (3) data-related (input parsing, output formatting, data types; together 33.5% of bugs), (4) library/dependency, (5) model-specific (truncation, hallucination); symptoms: compile error, runtime error, test failure, non-termination. Exact leaf names and percentages unverified (PDF unreachable). None of the six benchmarks reports this taxonomy.

**Audit cost estimates (per model, one pass, token-size based, not measured)**: LongWriter < $50; HelloBench $50-150; RepoTransBench 65-repo subset $50-200, full 1,897 ~$1-5k at Sonnet-tier prices; Commit0 lite $100s-$1k+; REPOCOD $30-100 plus hours of pytest; RepoMod-Bench $0.5-3k per full pass (1-5M tokens per task-run). Scale Fable 5.1 by roughly 3-5x relative to $2/$10 models.

## Appendix C. Research notes: statistical analysis plan (primary sources read where reachable: Anthropic post, rliable code, human-eval code, tau-bench code, baycomp/evalci, HELM summarize.py; papers via snippets)

**Data model**: one row per (model, benchmark, task, run) with primary score, judge score, output length, input/output tokens, $ at a frozen dated price sheet, wall-clock split into model latency / queue-and-rate-limit wait / tool execution, cluster id (repo or task family). Task = sampling unit; run = nested replicate. Var(mean) = (B + W/k)/n: k runs shrink only within-task noise W; between-task B is irreducible (Miller 2024, arXiv 2411.00640).

**Per-benchmark score + CI**: mean over tasks of per-task mean over runs. CLT SE on per-task means, 95% CI; cluster-robust SE when tasks share a repo (Miller: naive SEs >3x too narrow on popular evals); report design effect. For n < ~200 tasks use Wilson or Beta-Binomial Bayesian intervals (Bowyer, Aitchison & Ivanova, ICML 2025, arXiv 2503.01747); BCa bootstrap over tasks for continuous metrics. pass@k via Chen et al. 2021 unbiased estimator; reliability via tau-bench pass^k = E_task[C(c,k)/C(n,k)]; task-level bootstrap CIs around both.

**Paired comparisons (primary inference)**: per-task paired differences d_i, SE from Var(d) = (sA^2 + sB^2 - 2 rho sA sB)/n; frontier models show per-task rho ~0.3-0.7, so pairing cuts variance materially (Miller rec. 4). Exact McNemar for 0/1 with k=1; paired permutation/bootstrap as metric-agnostic default, resampling tasks and keeping all runs of a task together.

**Aggregation hierarchy (pre-register)**:
- Primary: per-benchmark paired differences on each benchmark's pre-declared primary metric, shown as a forest plot. No single composite as the primary claim (HELM: no universal aggregation exists; Colombo et al. 2022 arXiv 2202.03799: renormalising before averaging does not fix ranking instability).
- Secondary 1: rank aggregation, mean rank / Borda (= Kemeny with 3 models); HELM mean win rate is a Borda variant (Colombo; Rofin et al. 2023 Vote'n'Rank).
- Secondary 2: normalise each benchmark with declared floor (random/trivial baseline) and ceiling, then IQM and optimality gap with stratified bootstrap CIs (Agarwal et al. 2021; rliable `trim_mean(0.25)`, StratifiedBootstrap, 50,000 reps) and probability of improvement P(X>Y) via Mann-Whitney with ties = 1/2, meaningful if CI excludes 0.5.
- Secondary 3: Friedman + Nemenyi CD diagram labelled descriptive. With k=3 models and N=6 benchmarks CD = 1.35 on a 1-3 rank scale; exact Wilcoxon minimum two-sided p = 0.031 (unanimous dominance only). Replace with Bayesian signed-rank + ROPE (Benavoli et al. 2017, JMLR 18:77; `baycomp.two_on_multiple`), ROPE per benchmark pre-registered (e.g. 2 pass-rate points).

**Runs per task**: fixed k for all models (unequal k invites cherry-picking); Agarwal 3-10 runs; Bouthillier et al. 2021: randomise variance sources rather than fix seeds, declare A > B only if P(A beats B in one run) > 0.75. Prefer more tasks once W/k << B.

**Cost and time**: log tokens per call; compute $ as a pure function of tokens and a dated frozen price sheet (Kapoor et al. 2024 for $ at market rates; the tokens-plus-frozen-sheet rule is a synthesis, no primary source). Cost is right-skewed: median and mean $ with BCa CIs, plus p95. Pareto frontier accuracy vs mean $ with bootstrap bands, convex non-dominated set (Kapoor). Wall-clock: p50/p95, separate rate-limit waits; interleave models in time; treat as secondary and confounded otherwise.

**Multiple comparisons**: family = 3 pairs x 6 benchmarks = 18 primary tests per metric; Holm step-down for FWER on primary claims; Benjamini-Hochberg only for exploratory secondary metrics; correct for every test performed. "Which model is best" needs a Multiple-Comparisons-with-the-Best confidence set, not per-model CIs (Leaderboard Lottery, ICML 2026).

**Pre-registration**: OSF or SHA-256-hashed git tag, before any run: hypotheses, primary metric per benchmark, normalisation floors/ceilings, k, exclusion rules (timeouts, infra failures), cluster definition, ROPE per benchmark, correction family, judge-validation threshold, aggregation hierarchy. List deviations (Nosek et al. 2018; Gelman & Loken forking paths). Precedents: IatroBench OSF, CMU "preregister for the next LLM".

**Judge/task validation**: stratified human sample; Cohen's kappa (2 raters) or Krippendorff's alpha (>= 2, ordinal); alpha >= 0.80 reliable, 0.667 tentative; CIs on kappa/alpha; swap A/B order for position bias.

**Power table** (paired, alpha 0.05 two-sided, power 0.80, n = 7.85 * Var(d)/delta^2, Var(d) = 2B(1-rho) + 2W/k; main scenario B = 1/12, W = 1/6, rho = 0.5):
| k runs/task | delta = 5 pts | 10 pts | 15 pts |
|---|---|---|---|
| 1 | 1,309 tasks | 328 | 146 |
| 3 | 611 | 153 | 68 |
| 5 | 471 | 118 | 53 |
| infinite | 262 | 66 | 30 |
Inverse: 50 tasks with k=3 detects ~18-point gaps; 100 tasks ~12; 200 tasks ~9. Miller's own example: ~969 questions for a 3-point difference, recommends >= 1,000 questions for new evals. Card et al. 2020: MDE +5.26 on WNLI (147 items). Multiply n by the design effect if clustered. Distinguish "null" (CI excludes the smallest effect of interest) from "underpowered" (CI still admits it). Expect most 3-model pairwise results on 50-task sub-benchmarks to be underpowered, and say so.

**Rejection pitfalls**: raw heterogeneous averaging or post-hoc normalisation; counting n*k runs as independent (41-48x understated variance in one GSM8K case); naive SEs with clustered tasks; unpaired tests on paired data; CLT intervals on 30-100 tasks; plug-in pass@k; uncorrected 18+ tests or winner from per-model CIs; Friedman "significance" at N=6 or non-significance read as equivalence without ROPE; $ only or tokens only, mean cost without skew, wall-clock without rate-limit separation; judge scores without kappa/alpha and position-bias check; post-hoc exclusions; no pre-registration.

**Tools**: rliable, baycomp, evalci, errorbars (Miller reimplementation), scipy, human-eval and tau-bench estimators, Inspect eval logs as the raw record.

## Appendix B. Research notes: benchmark design science (snippets of primary sources; arxiv/openai/metr blocked at proxy)

**Construct validity**: state construct and intended use, never claim general capability from a bundle (Raji et al. 2021, arXiv 2111.15366). Four criteria: validity, reliability, statistical power (detect ~1% improvements), no artifact shortcuts (Bowman & Dahl, NAACL 2021). Report per-task results and ranking sensitivity to task subsets; benchmarks are stateful and erode with reuse (Dehghani et al. 2021, "Benchmark Lottery", arXiv 2107.07002). Top-down scenario taxonomy, declare what is not covered, evaluate all models on all scenarios under identical conditions, multiple metrics jointly (HELM, arXiv 2211.09110). Distinguish model-developer vs downstream-developer benchmarks (Kapoor et al. 2024, arXiv 2407.01502).

**Task curation**: human-validate every task with a written rubric and 0-3 severity on (a) underspecification and (b) tests rejecting valid solutions; discard 2-3 (SWE-bench Verified, OpenAI Aug 2024: 93 annotators, 1,699 tasks, 500 survivors). Screen for solution leakage and weak tests (SWE-Bench+, arXiv 2410.06992: 32.67% of successes leaked, 31.08% weak tests, resolution 12.47% to 3.97%). Adversarially strengthen tests (UTBoost arXiv 2506.09289; SWE-ABS arXiv 2603.00520: 251/500 Verified strengthened, -14.56 pp, rank correlation 0.82). Audit the unsolved tail: OpenAI "Why we no longer evaluate SWE-bench Verified" (2026-02-23) found >= 59.4% of frequently failed problems had tests rejecting correct solutions. Human baselines under agent-identical conditions with qualified baseliners (METR HCAST, arXiv 2503.17354); critique that success-only averaging biases durations low. Keep an errata file (LiveCodeBench ERRATA.md). Per-sample network-isolated sandboxes with message/token/time/cost limits (Inspect sandboxing docs).

**Contamination**: time-segment tasks by creation date, score only post-cutoff tasks (LiveCodeBench, ICLR 2025). Scheduled refresh with frozen named splits (SWE-bench-Live, 50 issues/month; SWE-rebench, NeurIPS 2025, arXiv 2505.20411). Fix deadline first, build test set after (K Prize: winner 7.5% vs ~75% on Verified). Statistical contamination test with log-probs (Oren et al., ICLR 2024, arXiv 2310.17623; needs canonical ordering). Guided-completion memorization probe (Golchin & Surdeanu, ICLR 2024). Agentic memorization control: file-path localization from issue text alone, in-benchmark vs out-of-benchmark repos (SWE-Bench Illusion, NeurIPS 2025, arXiv 2506.12286: 76% vs <= 53%). Encrypt published trajectories, request training exclusion (HAL harness; METR hcast-public).

**Harness & reproducibility**: pin prompts, task config version, commit hash (lm-eval task guide; Biderman et al. 2024, arXiv 2405.14782). Log every sample's input/output/target/score/transcript/token usage/generation config (Inspect .eval logs, `--log-model-api`). Separate dataset / solver / scorer so scaffolds swap without changing tasks (Inspect; METR deprecated its Task Standard in favour of Inspect). Containerize, cache by run_id, re-grade from logs (SWE-bench harness). Never copy numbers from other papers (HELM). Report elicitation protocol; classify failures spurious / tradeoff / real; scaffold choice can flip rankings (METR elicitation guidelines 2024; METR Jan 2025 update).

**Cost & efficiency**: pair every accuracy with inference cost, plot Pareto frontier; simple retry baselines match complex agents (Kapoor et al. 2024). Report dollars and tokens, pricing date, caching treatment (HAL, ICLR 2026, arXiv 2510.11977: 21,730 rollouts, ~$40k, fewer than a third of models on any frontier). Inspect logs for shortcuts (HAL found agents searching HuggingFace for the benchmark). Treat reasoning effort as a variable: higher effort reduced accuracy in a majority of HAL runs. Provide held-out tasks.

**Statistics pointers**: CIs on every number, repeated runs (Epoch: 16 runs on GPQA Diamond, 8 on MATH L5, +-1 SE). Clustered SEs when items share a repo (Miller 2024, up to 3x). Hierarchical bootstrap over task families (METR). Expected performance vs budget, not best-of-N (Dodge et al. 2019). BetterBench headline failure: most benchmarks report no significance and are not replicable.

**Judging**: prefer executable ground truth (LiveBench). If LLM judge: swap order, control verbosity, validate vs humans (Zheng et al. 2023: 65% position consistency). Never let a model family judge itself without cross-family control (Panickssery et al., NeurIPS 2024). Report chance-corrected agreement, not percent agreement (Thakur et al. 2024 "Judging the Judges"); Krippendorff alpha conventions 0.8 / 0.667 are from content-analysis literature.

**Documentation & release**: Datasheets (Gebru et al.), model-card style eval reporting (Mitchell et al.). NeurIPS D&B bar: reviewer-accessible URL, Croissant metadata (mandatory since 2025), license, hosting/maintenance plan. Replication script, uncertainty quantification, code docs (BetterBench, arXiv 2411.12990; 40-46 criteria depending on version; five lifecycle phases).

**Governance**: versioning, errata channel, retirement criterion, frozen vs live split policy (BetterBench lifecycle; SWE-bench-Live; LiveCodeBench v1-v6).

**Eight post-release embarrassments** (what reviewers will probe for): solutions in issue text; weak tests passing wrong patches; tests rejecting correct solutions in the hard tail; memorization of the 500 Verified tasks; collapse on post-cutoff tasks (K Prize 7.5%); agents gaming tasks (HAL); expensive agents beaten by retry baselines once cost shown; replacement benchmark (SWE-bench Pro) reportedly ~30% flawed (secondary source only).

## Appendix A. Research notes: modernization domain, models, pricing (fetched 2026-10-26)

Sandbox egress allowed direct fetches only to Anthropic domains; everything else is from search-engine snippets of the named primary source. Marked accordingly.

**LinkedIn post** urn:li:activity:7516561629614919680: login-walled, not indexed, not retrievable. Author, text and replies unknown. Do not cite it as context; ask the user to paste it.

**Practitioner success criteria (industry)**
- AWS Transform mainframe: functional-equivalence testing by replaying batch/online scenarios and comparing output datasets and 3270 screens; line-level traceability to source; human review of an equivalence report. No published accuracy methodology. (aws.amazon.com blogs, docs.aws.amazon.com/m2 apptest) [snippet]
- IBM watsonx Code Assistant for Z: "Automated Testing of COBOL to Java Transformation", FSE 2025 industry, arXiv 2504.10548. Symbolic execution over COBOL paragraph paths generates JUnit tests against translated Java; byte-level packed-decimal modelling; mocks DB2/CICS/files. [snippet]
- Google "Migrating Code at Scale with LLMs at Google", FSE 2025, arXiv 2504.09691: 39 migrations, 595 changes, 93,574 edits, 74.45% of changes LLM-authored, ~50% time reduction. Oracle = build + existing tests + human review (LSC flow; SWE-at-Google ch. 22). [snippet]
- Meta ACH mutation-guided test generation, FSE 2025, arXiv 2501.12862: generate mutants then tests that kill them; 73% engineer acceptance. Relevant as test-strength oracle. [snippet]
- Microsoft/GitHub Copilot Java/.NET modernization: build-before-start, OpenRewrite recipes, iterative build-fix, unit-test "behavioral integrity", CVE scan. [snippet]
- Mechanical Orchard Imogen: characterization tests generated from observed mainframe behavior, parallel run with equivalence monitoring. Vendor claims only. Thoughtworks CodeConcise: plain-GenAI reverse engineering rated ~60% accurate by client SMEs (martinfowler.com/articles/legacy-modernization-gen-ai.html). Cognition Devin COBOL (Apr 2026): batch tractable, live transactional "out of reach today".
- OpenAI "low-resource programming languages" (2026-10-19): private COBOL migration eval, success = byte-for-byte output match; GPT-6.1 Sol 86.6% low effort, 97.9% high effort (one outlet). Private, vendor-run. [snippet]

**Independent / academic**
- Pan et al. "Lost in Translation", ICSE 2024, arXiv 2308.03109: correct translations 2.1 to 47.3%; 1,748 failures labelled into a 15-category bug taxonomy (syntactic, semantic/data-type, API mismatch, I/O, dependency, ...). Artifact github.com/Intelligent-CAT-Lab/PLTranslationEmpirical.
- DARPA TRACTOR: MIT Lincoln Lab independent T&E; C batteries every 6 months; scores functional correctness, safety (unsafe usage), idiomaticity, performance. arXiv 2609.25121.
- SWE Refactor Bench, arXiv 2608.23564 (Aug 2026): 20 whole-repo stack migrations; 3-stage scoring (migration audit, fixed behavioural tests, 6 independent agents hunting hidden behavioural diffs). 28/520 runs (5.4%) pass all three; best 47.0/100 (Claude Opus 5, Claude Code xhigh); language rewrites 5.6 vs build-toolchain rewrites 31.4.
- FreshBrew, arXiv 2510.04852: 228 Java repos to JDK 17/21; success = compiles + original tests pass unmodified + line coverage drop <= 5 pp; best 52.3%.
- MigrationBench, Amazon, arXiv 2505.09569: 5,102 Java 8 Maven repos (MIT/Apache); minimal vs maximal migration; Claude 4.5 Sonnet agent 71.67% / 53.33%. HF: AmazonScience/migration-bench-java-full.
- Factory Legacy-Bench (Apr 2026): hundreds of tasks (COBOL ~46%, Java 7 ~32%, BASIC/C89/Fortran/Assembly ~5-6% each), hidden tests, Harbor-compatible; top 42.5%; 31 of 44 unsolved are COBOL. Vendor-run. docs.factory.ai/benchmarks/legacy-bench
- RepoMod-Bench (Modelcode.ai), arXiv 2602.22518 (Feb 2026): 21 repos, 8 languages, 1.6M LOC, 11,616 hidden implementation-agnostic tests; pass rate 91.3% (<10K LOC) to 15.3% (>50K LOC).
- RepoTransBench, TSE 2026: 1,897 repo-level translation samples, 13 language pairs, executable tests; best method 32.8%.

**LLM-independent equivalence oracles**: Diffy (opendiffy, with secondary instance to measure nondeterministic noise), GoReplay, shadow testing; Hypothesis Ghostwriter `--equivalent`, jqwik; mutation testing PIT / Stryker / mutmut / cosmic-ray (community thresholds 60 low / 80 high, no vendor standard); SymDiff, RustAssure (KLEE over LLVM IR of C and Rust, arXiv 2510.07604), VERT (arXiv 2404.18852), CINDER; FreshBrew coverage-preservation rule; byte-identical output comparison.

**Raw material with human-performed migrations and non-LLM oracles**
| Source | Migration | Oracle | License |
|---|---|---|---|
| AWS CardDemo (github.com/aws-samples/aws-mainframe-modernization-carddemo) | COBOL/CICS/BMS/VSAM/JCL | batch output datasets, screens; no unit tests | Apache-2.0 |
| NIST COBOL85 suite via GnuCOBOL tests | COBOL semantics | ~9,688 tests | public domain / GPL compiler |
| uutils/coreutils | C to Rust | GNU coreutils suite, 645/690 pass v0.10 | MIT |
| sudo-rs | C to Rust | compliance suite runs against original or port (`SUDO_UNDER_TEST`) | MIT/Apache-2.0 |
| zlib-rs | C to Rust | zlib-ng suite, fuzz, byte-exact streams | Zlib |
| LAPACK TESTING/ | Fortran to X | reference drivers | BSD-3 |
| SciPy Fortran-removal PRs | Fortran to C/Cython | full SciPy suite, real human commits | BSD-3 |
| MigrationBench repos | Java 8 to 17/21 | existing tests | MIT/Apache |
| PyComply corpus (Malloy & Power 2017/2019) | Py2 to Py3 | project suites, real commits | varies |
| gnulib-tool rewrite | shell to Python | identical-output goal | GPL |
Not found as public OSS with history: AngularJS to Angular, VB6 to .NET, Perl to Python.

**Models and pricing (USD per 1M tokens)**
| | Claude Fable 5.1 `claude-fable-5-1` | Gemini 4 Argon `gemini-4-argon` | GPT-6.1 Sol `gpt-6.1-sol` |
|---|---|---|---|
| Input / Output | $10 / $50 (thinking billed as output) [fetched, Anthropic] | $2 / $10, doubling to $4 / $20 on 2026-12-01 [snippet] | $2 / $10; $4 / $15 above 272K context [snippet] |
| Cached input | $0.25 | $0.10 implicit | $0.10 |
| Batch | 50% off | not confirmed | 50% off |
| Context / max output | 1M / 128K | 1,048,576 shared / 65,536 default | ~1.05M / 128K |
| Effort | low/medium/high(default)/xhigh/max | low/medium(default)/high | low/medium(default)/high/xhigh/max |
"6.1 Sol" = OpenAI GPT-6.1 Sol, high confidence. Google and OpenAI prices are medium confidence (vendor pages unreachable, 4+ aggregators agree). Note: "high effort" is the default for Fable 5.1 but one notch above default for the other two; also Fable 5.1 offers xhigh/max above "high". Effort parity is a design decision, not a given.

**Frontier level today**: Vals Terminal-Bench 4.0 (2026-10-24, independent): Fable 5.1 58.08, Argon 57.58, Sol 55.05, Opus 5.5 65.15. No vendor publishes SWE-bench Verified any more; official board stale since 2026-02-26. Modernization-specific numbers are far from saturated (SWE Refactor Bench 5.4% full pass; RepoMod-Bench 15.3% on >50K LOC; Legacy-Bench <= 42.5%).
