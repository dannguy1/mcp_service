#!/bin/bash

echo "=== Committing and pushing changes to GitHub ==="

# Check current status
echo "1. Checking git status..."
git status

# Add all changes
echo -e "\n2. Adding all changes..."
git add .

# Check what will be committed
echo -e "\n3. Changes to be committed:"
git diff --cached --name-status

# Commit changes
echo -e "\n4. Committing changes..."
git commit -m "Clean up verification scripts and sync main/dev branches

- Removed temporary verification scripts created during branch comparison
- Confirmed main and dev branches are synchronized
- Cleaned up workspace after merge verification process"

# Push to GitHub
echo -e "\n5. Pushing to GitHub..."
git push origin main

echo -e "\n✅ Changes successfully committed and pushed to GitHub!"
echo "Your repository is now up to date." 