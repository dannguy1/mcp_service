#!/bin/bash

echo "=== Fetching latest changes from remote ==="
git fetch origin

echo -e "\n=== Commits in dev that are NOT in main ==="
echo "These are the commits that exist in dev branch but not in main:"
git log --oneline main..origin/dev

echo -e "\n=== Files that are different in dev compared to main ==="
echo "These files have been modified, added, or deleted in dev:"
git diff --name-status main origin/dev

echo -e "\n=== Detailed changes in dev (file by file) ==="
echo "Showing the actual content differences:"
git diff main origin/dev

echo -e "\n=== Summary of changes ==="
echo "Statistics of what changed:"
git diff --stat main origin/dev 