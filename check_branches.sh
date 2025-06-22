#!/bin/bash

echo "=== Git Repository Status ==="
git status

echo -e "\n=== Current Branch ==="
git branch

echo -e "\n=== Remote Branches ==="
git branch -r

echo -e "\n=== Fetching latest changes ==="
git fetch origin

echo -e "\n=== Commits in dev but not in main ==="
git log --oneline main..origin/dev

echo -e "\n=== Commits in main but not in dev ==="
git log --oneline origin/dev..main

echo -e "\n=== Files changed in dev compared to main ==="
git diff --name-only main origin/dev

echo -e "\n=== Summary of changes in dev ==="
git diff --stat main origin/dev 