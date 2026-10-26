# Pre-registration: LegacyBench pilot v0

Status: DRAFT. Not yet frozen. Run `bash prereg/hash.sh` to freeze; the hash and git
tag are the registration. After freezing, any change to this file, `tasks/pilot.yaml`,
`legacybench/prices.yaml` or the solver/scorer code must be listed under Deviations
in the final report.

## 1. Purpose

A $200 pilot. It does not rank models. It (a) measures each model's real output
ceiling, (b) validates the harness end to end, (c) measures per-task cost, time and
score variance for the full study's power analysis, (d) gives a descriptive first
look at single-shot versus agentic migration on size-stratified tasks.

## 2. Models and settings

| Model | Inspect name | Effort setting | Max output requested |
|---|---|---|---|
| Claude Fable 5.1 | anthropic/claude-fable-5-1 | high (vendor default) | provider default; probe: 128000 |
| Gemini 4 Argon | google/gemini-4-argon | high | provider default; probe: 1048576 |
| GPT-6.1 Sol | openai/gpt-6.1-sol | high | provider default; probe: 128000 |
| GPT-6 Astra | openai/gpt-6-astra | high | provider default; probe: 128000 |

Effort "high" for all is the registered headline. Note that this is the default for
Fable and above default for the others; Fable also exposes xhigh and max, which are
not used. Prices: `legacybench/prices.yaml` as of [DATE], Astra entry to be filled.

## 3. Probe protocol (Claim A)

`legacybench/probe/ceiling.py` with lengths 2000, 8000, 20000, 60000 functions
(about 28K, 115K, 290K, 870K output tokens). One call per length per model; one
retry only if the first call stops below the vendor's documented cap with
stop_reason other than `max_tokens`. Record: valid lines, stop reason, output and
reasoning tokens, decode tokens per second, provider errors. The measured cap is the
largest length completed in full.

## 4. Tasks

`tasks/pilot.yaml` (hash below). Six single-shot tasks in strata S, M, L (two
each) run in both arms; ten breadth tasks (B) run in the agentic arm only, on
Fable, Argon and Sol (Astra omitted from B to fit the budget). k = 1 run per task.
Source: FreshBrew full_dataset.yaml, JDK 8 to 17. Public split only; contamination
is not assessed in the pilot.

## 5. Oracle and primary metric

Primary metric per task: all required gates pass (binary). Gates in order: build on
JDK 17; all original tests pass; src/test byte-for-byte unchanged versus the
reference copy; tests run >= baseline; all class files major version >= 61;
FreshBrew coverage guard, (after / before) - 1 > -0.05 relative. Per-gate results
are recorded so failures are attributable.

## 6. Arms

Single-shot: whole repository emitted in one response, `emit_all_files=True`, no
tools. Agentic: shared minimal scaffold (bash, text editor, submit), same system
prompt for all models. Caps per sample from `default_limits` in the manifest, with
per-model cost caps in the workflow inputs: Fable $9 single-shot / $5 agentic;
others $2 / $1.50.

## 7. Analysis (descriptive only)

Per model x arm: pass count, pass rate with Wilson 95% interval, cost median,
mean, p95 and total, time p50 and p95 with wait time separated. Single-shot:
truncation rate, output and reasoning tokens, files written. Minimum detectable
effect at the pilot's n is printed beside every table. No hypothesis is tested;
H1 to H3 from the design brief are stated for the full study and only looked at
descriptively here.

## 8. Exclusions

Samples that fail for infrastructure reasons (sandbox build error, provider 5xx
after Inspect's retries) are reported separately and not counted as model
failures. Samples stopped by a cost, token, message or time cap count as failures
and are flagged with the cap that fired.

## 9. Hashes

Filled by `prereg/hash.sh`.
