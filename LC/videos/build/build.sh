#!/usr/bin/env bash
# Build one video in the Higgsfield sandbox.
#   bash build.sh <video_dir> [render]
# <video_dir> must hold scenes.json and assets.json ({"audio": {"NN": url}, "heroes": {"N": url}}).
set -euo pipefail
V="$1"; MODE="${2:-render}"
cd "$(dirname "$0")"
ROOT="$(pwd)"
cd "$V"
mkdir -p audio media proj renders
python3 - <<'EOF'
import json, os, subprocess
a = json.load(open("assets.json"))
jobs = []
for k, url in a["audio"].items():
    jobs.append(("audio/s%s.mp3" % k, url))
for n, url in a["heroes"].items():
    jobs.append(("media/hero%02d.png" % int(n), url))
for path, url in jobs:
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        continue
    subprocess.run(["curl", "-fsSL", "--retry", "4", "--retry-delay", "2", "-o", path, url], check=True)
print("downloaded", len(jobs), "assets")
EOF
# durations
python3 - <<'EOF'
import json, subprocess, glob, os
d = {}
for f in sorted(glob.glob("audio/s*.mp3")):
    key = os.path.basename(f)[1:3]
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    d[key] = float(out)
json.dump(d, open("durations.json", "w"), indent=1)
print("durations:", len(d), "files, total %.1f s" % sum(d.values()))
EOF
python3 "$ROOT/captions.py" . | tail -3
python3 "$ROOT/gen_edit.py" .
if ! ls proj/fonts 2>/dev/null | grep -q -i inter; then
  # first build creates the project dir, then fonts are vendored into it
  set +e; higgsedit build edit.jsx > build_first.log 2>&1; set -e
  higgsedit fonts add proj Inter "Inter:700" "JetBrains Mono" "JetBrains Mono:700" | tail -2
fi
PROOF="${PROOF_TIMES:-}" higgsedit build edit.jsx 2>&1 | grep -v '^\[page\]' | tail -5
if [ "$MODE" = "render" ]; then
  echo "RENDER START $(date +%T)"
  higgsedit render proj --engine node --workers 5 --out renders/final.mp4 > render.log 2>&1
  echo "RENDER END $(date +%T)"
  ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height -of compact renders/final.mp4
fi
echo "BUILD DONE"
