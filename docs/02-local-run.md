# Running the pilot locally

A checklist for running the $200 pilot on one machine. Follow the order; the
pre-registration freeze in step 4 is what makes the result a pilot rather than a demo.

## 0. Prerequisites

- Docker Desktop or Docker Engine with at least 8 GB RAM and 40 GB disk allotted.
  Apple Silicon works; the image resolves JDK paths for arm64 at build time.
- Python 3.11 or newer. `pip install -e ".[dev]"` from the repo root, then `pytest`.
- API keys as environment variables: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`,
  `OPENAI_API_KEY`. Set a hard spend cap in each vendor console before anything else;
  the harness caps per sample, the console caps the account.
- Network at build time only. Containers run with no network.

## 1. Prices and model names

Open `legacybench/prices.yaml`. Verify the Google and OpenAI entries on the vendor
pricing pages and fill the GPT-6 Astra entry; the harness refuses to run a model whose
entry is incomplete. Confirm the exact API model identifiers for all four and correct
the keys in that file if a vendor uses a different string. Note Argon's scheduled price
change on 2026-12-01.

## 2. Build and verify the sandbox image

```bash
bash scripts/build_image.sh tasks/pilot.yaml      # clones 16 repos at pinned commits, builds image (20 to 60 min)
python scripts/verify_image.py tasks/pilot.yaml   # every repo must pass its tests on JDK 8 inside the image
```

If a repo fails verification, remove it from `tasks/pilot.yaml` and note the removal
as a deviation in `prereg/PREREG.md` before freezing.

## 3. Dry run with one cheap sample

```bash
export INSPECT_LOG_DIR=logs
inspect eval legacybench/tasks.py@pilot_agentic --model google/gemini-4-argon \
  -T strata=S --limit 1 --cost-limit 1 --reasoning-effort high
inspect view   # open the trajectory, confirm the agent could run mvn and the scorer produced per-gate results
```

Then one single-shot sample the same way with `pilot_single_shot`. These two samples are
not part of the pilot; they confirm the plumbing. Expect to spend under $3.

## 4. Freeze the pre-registration

Edit `prereg/PREREG.md` (effort settings, deviations so far, date), then:

```bash
bash prereg/hash.sh
git push origin prereg-pilot-v0
```

Everything after this point is a scored run. Changing the registered files afterwards
is allowed only with a logged deviation.

## 5. Output-ceiling probe

One model at a time. Request the vendor's documented ceiling; a rejected request is a
finding, not a failure.

```bash
inspect eval legacybench/probe/ceiling.py --model google/gemini-4-argon      --max-tokens 1048576 --reasoning-effort high --cost-limit 12
inspect eval legacybench/probe/ceiling.py --model anthropic/claude-fable-5-1 --max-tokens 128000  --reasoning-effort high --cost-limit 8
inspect eval legacybench/probe/ceiling.py --model openai/gpt-6.1-sol         --max-tokens 128000  --reasoning-effort high --cost-limit 3
inspect eval legacybench/probe/ceiling.py --model openai/gpt-6-astra         --max-tokens 128000  --reasoning-effort high --cost-limit 3
```

A near-1M decode can take an hour. Run the Argon probe when you can leave the machine.

## 6. Arms

Single-shot first (cheaper, no sandbox work by the model), then agentic. One model per
command, interleave models across the day so time-of-day latency is not confounded
with model.

```bash
# single-shot, strata S,M,L
inspect eval legacybench/tasks.py@pilot_single_shot --model anthropic/claude-fable-5-1 -T strata=S,M,L --cost-limit 9   --reasoning-effort high
inspect eval legacybench/tasks.py@pilot_single_shot --model google/gemini-4-argon      -T strata=S,M,L --cost-limit 2   --reasoning-effort high
inspect eval legacybench/tasks.py@pilot_single_shot --model openai/gpt-6.1-sol         -T strata=S,M,L --cost-limit 2   --reasoning-effort high
inspect eval legacybench/tasks.py@pilot_single_shot --model openai/gpt-6-astra         -T strata=S,M,L --cost-limit 2   --reasoning-effort high

# agentic, strata S,M,L for all four; breadth B for three
inspect eval legacybench/tasks.py@pilot_agentic --model anthropic/claude-fable-5-1 -T strata=S,M,L   --cost-limit 5   --reasoning-effort high --max-samples 2
inspect eval legacybench/tasks.py@pilot_agentic --model google/gemini-4-argon      -T strata=S,M,L,B --cost-limit 1.5 --reasoning-effort high --max-samples 4
inspect eval legacybench/tasks.py@pilot_agentic --model openai/gpt-6.1-sol         -T strata=S,M,L,B --cost-limit 1.5 --reasoning-effort high --max-samples 4
inspect eval legacybench/tasks.py@pilot_agentic --model openai/gpt-6-astra         -T strata=S,M,L   --cost-limit 1.5 --reasoning-effort high --max-samples 2
```

`--max-samples` is how many sandboxes run at once; each gets 2 CPUs and 6 GB from
`docker/compose.yaml`. Lower it on a small machine.

Running total at any point:

```bash
python -m legacybench.analysis.report logs --out reports/pilot && cat reports/pilot/summary.md
```

## 7. Report

`reports/pilot/ledger.csv` has one row per sample with tokens, dollars, time split and
per-gate results. `summary.md` is descriptive and prints the minimum detectable effect
beside each row. Write the plain-language note from it, first paragraph stating what
the pilot cannot claim.

## Troubleshooting

- **A model id is rejected by the provider.** Fix the key in `prices.yaml` and the
  `--model` string. If this happens after the freeze, log it as a deviation.
- **Build fails for one repo at image build time.** The build tolerates it; `verify_image.py`
  will flag the repo. Drop it from the manifest, log the deviation.
- **`text_editor` tool errors inside the sandbox.** The image must contain
  `inspect-tool-support`; rebuild with the current Dockerfile.
- **Maven tries to go online inside the sandbox.** A dependency was not warmed. Add the
  missing goal to the warm-up loop in the Dockerfile and rebuild. Do not remove
  `network_mode: none`.
- **Rate limits.** Inspect retries with backoff; the wait shows up as `wait_time_s` in the
  ledger, separated from model time. Reduce `--max-samples` or `--max-connections`.
- **A sample hits a cap.** It is scored as a failure and the cap is recorded in the
  `limit` column. That is the intended behavior under the registered exclusion rule.
- **Mock smoke test fails on tiktoken download.** Allow network once or set
  `TIKTOKEN_CACHE_DIR` to a directory that already holds the encoding file.
