#!/usr/bin/env bash
# One-command GitHub deploy for the connector.
#
#   bash deploy_to_github.sh <github-username> [repo-name] [--public]
#
# Uses the GitHub CLI (`gh`) if installed; otherwise falls back to plain git
# and tells you the exact push command.
set -euo pipefail
cd "$(dirname "$0")"

USER_NAME="${1:?usage: bash deploy_to_github.sh <github-username> [repo-name] [--public]}"
REPO="${2:-agent-studio-woocommerce-connector}"
VISIBILITY="--private"
[[ "${3:-}" == "--public" ]] && VISIBILITY="--public"

# Safety: never push secrets.
if [[ -f .env ]]; then
  echo "ERROR: .env exists. It is gitignored, but remove it before pushing anyway." >&2
  exit 1
fi

git init -q 2>/dev/null || true
git add .
git commit -m "Agent Studio — WooCommerce private connector (MCP)" >/dev/null 2>&1 || echo "(nothing new to commit)"
git branch -M main

if command -v gh >/dev/null 2>&1; then
  echo "Creating GitHub repo $USER_NAME/$REPO ($VISIBILITY) and pushing ..."
  gh repo create "$USER_NAME/$REPO" $VISIBILITY --source=. --remote=origin --push
  gh repo view "$USER_NAME/$REPO" --web >/dev/null 2>&1 || true
  echo "Done: https://github.com/$USER_NAME/$REPO"
else
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/$USER_NAME/$REPO.git"
  echo "GitHub CLI (gh) not found. Create an EMPTY repo at https://github.com/new"
  echo "  name: $REPO   (do NOT add a README/.gitignore — this repo has them)"
  echo "Then run:"
  echo "  git push -u origin main"
fi
