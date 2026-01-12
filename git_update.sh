#!/bin/bash

set -e

# Get information
USER=$(whoami)
HOST=$(hostname)
DATE=$(date "+%Y-%m-%d %H:%M:%S")
BRANCH=$(git branch --show-current)
OS=$(uname -s)

# Default commit message
DEFAULT_MSG="Update: $DATE by $USER@$HOST on $BRANCH [$OS]"

# Pull latest changes
echo "Pulling latest changes..."
git pull

# Check for changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Changes detected. Adding files..."
    git add .
    
    # Use provided message or default
    if [ $# -eq 1 ]; then
        MSG="$1"
        git commit -m "$MSG"$'\n\n'"Auto-update: $DATE by $USER@$HOST"
    else
        git commit -m "$DEFAULT_MSG"
    fi
    
    echo "Pushing changes..."
    git push origin "$BRANCH"
    echo "✓ Update completed successfully"
else
    echo "No changes to commit"
    echo "✓ Already up to date"
fi