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
git commit -m "Improve database connection test functionality

Backend Improvements:
- Enhanced error handling with specific exception types (authentication, timeout, connection failures)
- Added comprehensive input validation for required fields and data types
- Implemented proper timeout management (connection: 10s, overall: 15s, query: 5s)
- Added detailed response structure with error types and diagnostic information
- Improved error categorization (timeout, authentication, database_not_found, etc.)

Frontend Improvements:
- Enhanced error handling with field validation before API calls
- Improved error message extraction and display
- Added detailed test result display with connection details and error types
- Updated TypeScript types to support new detailed response structure
- Better user feedback with loading states and comprehensive results

Documentation and Testing:
- Created comprehensive PostgreSQL external connection setup guide
- Added diagnostic script for PostgreSQL configuration issues
- Created test script for improved database connection functionality
- Added detailed documentation of improvements and troubleshooting steps

This resolves the issue where external database connections (non-localhost) 
failed with generic error messages, now providing specific, actionable feedback."

# Push to GitHub
echo -e "\n5. Pushing to GitHub..."
git push origin main

echo -e "\n✅ Changes successfully committed and pushed to GitHub!"
echo "Your repository is now up to date." 