#!/bin/bash
set -e

USERNAME="$1"
PR_NUMBER="$2"
REPO="$3"
GH_TOKEN="$4"

WORKDIR="/home/baker/simulations/$USERNAME"
cd "$WORKDIR"

echo "Running Python files in $WORKDIR..."

LOG_FILE="simulation.log"
> "$LOG_FILE"

for file in *.py; do
  {
    echo "===== Running $file ====="
    python3 "$file"
  } >> "$LOG_FILE" 2>&1 || echo "$file failed." >> "$LOG_FILE"
done

echo "Uploading results..."

# Upload result files via GitHub REST API (e.g., using curl)
for f in *output*; do
  if [ -f "$f" ]; then
    curl -X POST \
      -H "Authorization: token $GH_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      https://api.github.com/repos/$REPO/issues/$PR_NUMBER/comments \
      -d "{\"body\":\"Uploaded result file \`$f\`. (not embedded here)\"}"
  fi
done

# Upload the log file as a comment
LOG_CONTENT=$(<"$LOG_FILE")
curl -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/issues/$PR_NUMBER/comments \
  -d "{\"body\":\"\`\`\`\n$LOG_CONTENT\n\`\`\`\"}"

echo "Done."

