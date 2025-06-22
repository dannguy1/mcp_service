# MCP Service Backend - Environment Configuration Guide

## Overview
This backend uses a single `.env` file for all configuration. Both the backend Python code and the shell scripts read from this file, ensuring a single source of truth for all environment variables.

## How Environment Variables Are Loaded
- **Python code**: Uses [`python-dotenv`](https://pypi.org/project/python-dotenv/) to load variables from `.env` automatically.
- **Shell scripts**: The `start_backend.sh` script sources the `.env` file so all variables are available to subprocesses (like `uvicorn`).

## How to Set Up
1. **Copy the template**
   ```bash
   cp backend/example.env backend/.env
   ```
2. **Edit `backend/.env`**
   - Fill in any secrets, passwords, or hostnames as needed for your environment.
   - Do **not** add comments or blank lines to `.env` (see below).

3. **Start the backend**
   ```bash
   ./scripts/start_backend.sh -b
   ```
   - This will load all variables from `.env` and start the backend in the background.

## Environment Variable Format
- Each line must be `KEY=VALUE` (no spaces around `=`)
- **No comments or blank lines** (for shell compatibility)
- If a value contains spaces, wrap it in quotes (e.g., `MY_VAR="some value"`)
- Do **not** use inline comments

## Example
See `backend/example.env` for a full list of supported variables and their default/example values.

## Why This Approach?
- **Single source of truth**: No more confusion between shell exports and Python config.
- **Easy to update**: Change config in one place, restart the backend, and you're done.
- **Works for both shell and Python**: No more duplicated or out-of-sync config.

## Troubleshooting
- If you add or change variables in `.env`, always restart the backend for changes to take effect.
- If you see errors about missing variables, check that `.env` is present and correctly formatted.
- If you need to add new config variables, add them to both `.env` and `example.env` for documentation.

## Security
- **Never commit `.env` with real secrets to version control.**
- Only commit `example.env` (with placeholder/example values) for documentation.

---

For further details, see the code comments in `scripts/start_backend.sh` and `backend/app/config/config.py`. 