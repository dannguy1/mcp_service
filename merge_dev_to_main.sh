#!/bin/bash

set -e  # Exit on any error

echo "=== Starting merge of dev into main ==="

# Step 1: Check current status
echo "1. Checking current git status..."
git status

# Step 2: Fetch latest changes
echo -e "\n2. Fetching latest changes from remote..."
git fetch origin

# Step 3: Check what commits are in dev but not in main
echo -e "\n3. Commits in dev that will be merged into main:"
git log --oneline main..origin/dev

# Step 4: Check for conflicts
echo -e "\n4. Checking for potential merge conflicts..."
git merge-tree $(git merge-base main origin/dev) main origin/dev

# Step 5: Perform the merge
echo -e "\n5. Merging dev into main..."
git merge origin/dev --no-edit

echo -e "\n=== Merge completed successfully! ==="
echo "Your main branch now contains all changes from dev."
echo -e "\nTo push the changes to remote:"
echo "git push origin main" 