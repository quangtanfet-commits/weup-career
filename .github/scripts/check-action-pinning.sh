#!/usr/bin/env bash
# Enforce that every THIRD-PARTY GitHub Action is pinned to a 40-char commit
# SHA (supply-chain hardening, N-6). First-party (actions/*, github/*) and
# local (./...) actions are allowed on tags by policy.
# Rationale + scope: docs/security/actions-sha-pinning-2026-06.md
set -euo pipefail

workflow_dir="${1:-.github/workflows}"
violations=0

while IFS= read -r raw; do
  # raw looks like: "uses: owner/action@<ref>"  → take the ref token only
  ref="$(printf '%s\n' "$raw" | sed -E 's/.*uses:[[:space:]]*//' | awk '{print $1}')"
  [ -z "$ref" ] && continue

  case "$ref" in
    ./*) continue ;;                 # local action — not external supply chain
    actions/*|github/*) continue ;;  # first-party (GitHub-owned) — tag allowed
  esac

  # Any remaining ref is third-party and MUST end in @<40 hex>.
  if ! printf '%s\n' "$ref" | grep -qE '@[0-9a-f]{40}$'; then
    echo "❌ UNPINNED third-party action: $ref"
    violations=$((violations + 1))
  fi
done < <(grep -rhoE 'uses:[[:space:]]*[^[:space:]]+' "$workflow_dir")

if [ "$violations" -gt 0 ]; then
  echo ""
  echo "$violations third-party action(s) not pinned to a 40-char commit SHA."
  echo "Resolve with: gh api repos/<owner>/<repo>/commits/<tag> --jq .sha"
  echo "then pin as:  uses: owner/action@<sha> # vX.Y.Z"
  exit 1
fi

echo "✅ All third-party actions are pinned to a 40-char commit SHA."
