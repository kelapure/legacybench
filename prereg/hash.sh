#!/usr/bin/env bash
# Freeze or verify the pre-registration.
#   bash prereg/hash.sh          -> writes prereg/HASHES.txt and creates tag prereg-pilot-v0
#   bash prereg/hash.sh --check  -> verifies the registered files are unchanged
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FILES=(prereg/PREREG.md tasks/pilot.yaml legacybench/prices.yaml legacybench/solvers/single_shot.py legacybench/solvers/agentic.py legacybench/scorers/gates.py legacybench/scorers/java_migration.py legacybench/probe/ceiling.py)

if [[ "${1:-}" == "--check" ]]; then
  if [[ ! -f prereg/HASHES.txt ]]; then
    echo "not frozen yet (no prereg/HASHES.txt); runs before freezing are pilots of the pilot" >&2
    exit 0
  fi
  sha256sum -c prereg/HASHES.txt
  exit $?
fi

sha256sum "${FILES[@]}" > prereg/HASHES.txt
echo "frozen $(date -u +%FT%TZ)" >> prereg/HASHES.txt
cat prereg/HASHES.txt
if git rev-parse -q --verify refs/tags/prereg-pilot-v0 >/dev/null; then
  echo "tag prereg-pilot-v0 already exists; not moving it" >&2
else
  git add prereg/HASHES.txt && git commit -q -m "Freeze pilot pre-registration" && git tag -a prereg-pilot-v0 -m "Pre-registration freeze"
  echo "tagged prereg-pilot-v0; push with: git push origin prereg-pilot-v0"
fi
