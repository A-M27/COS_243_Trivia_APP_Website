#!/usr/bin/env bash
# dev.sh: start the FastAPI backend and the Vite dev server in ONE terminal.
#
# Usage (from the flashcard/ folder):
#   bash dev.sh
#
# 1. Runs "npm run build" first. If the build has errors, it stops there.
# 2. Otherwise it starts both servers.
# Press Ctrl+C once to stop both.

cd "$(dirname "$0")" || exit 1

# When the script ends for ANY reason (Ctrl+C, or one server crashing),
# stop every process this script started.
cleanup() {
  trap - INT TERM EXIT
  echo
  echo "Stopping both servers..."
  kill 0 2>/dev/null
}
trap cleanup INT TERM EXIT

# Step 1: build first. This catches Svelte errors and keeps
# trivia/dist (what port 8000 serves at /trivia/) up to date.
echo "Building trivia/dist to check for errors..."
if ! (cd trivia && npm run build); then
  echo
  echo "BUILD FAILED: fix the errors above, then run bash dev.sh again."
  exit 1
fi
echo "Build OK."
echo

echo "==============================================="
echo " Open these (use localhost, not 127.0.0.1, so you stay logged in):"
echo "   Flashcards:  http://localhost:8000/"
echo "   Trivia:      http://localhost:8000/trivia/   (live code from Vite)"
echo " Vite runs in the background on :5173. You don't need to open it."
echo " Press Ctrl+C to stop both."
echo "==============================================="

# Each server's output gets a label so you can tell them apart.
# VITE_DEV=1 tells the templates to load live code from Vite (see web/routes.py).
VITE_DEV=1 uv run uvicorn main:app --reload 2>&1 | sed -u 's/^/[api]  /' &
(cd trivia && FORCE_COLOR=1 npm run dev 2>&1) | sed -u 's/^/[vite] /' &

# Wait until one of them stops; the EXIT trap then stops the other.
wait -n
