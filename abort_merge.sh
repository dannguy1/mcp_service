#!/bin/bash

echo "=== Aborting merge ==="
echo "This will reset your main branch to its state before the merge."

read -p "Are you sure you want to abort the merge? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git merge --abort
    echo "Merge aborted. Your main branch is back to its previous state."
else
    echo "Merge abort cancelled."
fi 