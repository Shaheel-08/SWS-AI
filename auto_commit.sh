#!/bin/bash

# auto_commit.sh — Automatically commit progress to GitHub
# Usage: bash auto_commit.sh &
# The & runs it in the background

echo "Starting auto-commit service..."
echo "Committing every 900 seconds (15 minutes)"
echo "Press Ctrl+C to stop"

while true; do
  # Add all changes
  git add .
  
  # Commit with timestamp
  git commit -m "progress: $(date '+%Y-%m-%d %H:%M:%S')"
  
  # Push to main branch
  git push origin main
  
  # Wait 900 seconds (15 minutes)
  sleep 900
done
