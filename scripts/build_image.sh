#!/usr/bin/env bash
# Clone every manifest repo at its pinned commit into docker/repos/<id>/, then
# build the sandbox image. Requires network at build time only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${1:-$ROOT/tasks/pilot.yaml}"
TAG="${IMAGE_TAG:-legacybench/java-migration:pilot-v0}"

mkdir -p "$ROOT/docker/repos"
python3 - "$MANIFEST" "$ROOT/docker/repos" <<'EOF'
import subprocess, sys, yaml, pathlib, shutil
manifest, out = sys.argv[1], pathlib.Path(sys.argv[2])
m = yaml.safe_load(open(manifest))
for t in m["tasks"]:
    d = out / t["id"].replace("/", "__")
    if (d / ".git").exists():
        head = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        if head == t["commit"]:
            print("ok", t["id"]); continue
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    subprocess.run(["git", "-C", str(d), "remote", "add", "origin", f"https://github.com/{t['repo']}.git"], check=True)
    subprocess.run(["git", "-C", str(d), "fetch", "-q", "--depth", "1", "origin", t["commit"]], check=True)
    subprocess.run(["git", "-C", str(d), "checkout", "-q", "FETCH_HEAD"], check=True)
    print("cloned", t["id"], t["commit"][:12])
EOF

docker build -f "$ROOT/docker/java-migration.Dockerfile" -t "$TAG" "$ROOT/docker"
echo "built $TAG"
