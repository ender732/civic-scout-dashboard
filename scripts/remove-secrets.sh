#!/usr/bin/env bash
set -euo pipefail
# Script: remove-secrets.sh
# Creates a cleaned mirrored repo with sensitive files removed using git-filter-repo.
# WARNING: This rewrites history in the mirrored repository only. You will need to
# push the cleaned mirror to your remote (force push) to replace history there.

REPO_DIR="$(pwd)"
CLEAN_DIR="${REPO_DIR}-cleaned.git"
SENSITIVE_PATHS=("packages/civic-scout-agent/.env")

echo "This will create a cleaned mirrored repo at: $CLEAN_DIR"
echo "Sensitive paths to remove: ${SENSITIVE_PATHS[*]}"

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo not found. Install it first: pip install git-filter-repo"
  echo "Alternatively, use the BFG tool. See README.md for instructions."
  exit 1
fi

if [ -d "$CLEAN_DIR" ]; then
  echo "Clean mirror already exists at $CLEAN_DIR — remove or rename it to continue."
  exit 1
fi

echo "Creating mirrored clone..."
git clone --mirror "$REPO_DIR" "$CLEAN_DIR"

cd "$CLEAN_DIR"

echo "Running git-filter-repo to remove sensitive paths..."
for p in "${SENSITIVE_PATHS[@]}"; do
  git filter-repo --invert-paths --paths "$p"
done

echo "Cleaned mirrored repo created at: $CLEAN_DIR"
echo "To replace your remote with the cleaned history, run (careful — this rewrites remote history):"
echo "  cd $CLEAN_DIR"
echo "  git remote add origin <your-remote-url>  # if not present"
echo "  git push --force --all origin"
echo "  git push --force --tags origin"

echo "After pushing, inform collaborators to re-clone the repository."
