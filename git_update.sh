#!/bin/bash

set -e

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Get timezone info
get_tz() {
    if command -v timedatectl &> /dev/null; then
        timedatectl show --property=Timezone --value 2>/dev/null || echo "Unknown"
    elif [ -f /etc/timezone ]; then
        cat /etc/timezone 2>/dev/null || echo "Unknown"
    else
        echo "${TZ:-"Not specified"}"
    fi
}

# Get info
USER=$(whoami)
HOST=$(hostname)
BRANCH=$(git branch --show-current)
DATE_LOCAL=$(date "+%Y-%m-%d %H:%M:%S")
DATE_UTC=$(date -u "+%Y-%m-%d %H:%M:%S")
TZ=$(get_tz)
OFFSET=$(date +%z | sed 's/^\([+-][0-9]\{2\}\)\([0-9]\{2\}\)$/\1:\2/')

# Default commit message
DEFAULT_MSG="Update: $DATE_LOCAL ($TZ UTC$OFFSET)"

echo -e "${GREEN}Git Update Script${NC}"
echo "User: $USER@$HOST"
echo "Branch: $BRANCH"
echo "Local: $DATE_LOCAL"
echo "UTC: $DATE_UTC"
echo "Timezone: $TZ (UTC$OFFSET)"
echo ""

# Pull changes
git pull origin "$BRANCH"

# Check for changes
if [ -n "$(git status --porcelain)" ]; then
    git add .
    
    if [ $# -eq 1 ]; then
        MSG="$1"$'\n\n'"Timestamp: $DATE_UTC UTC | $DATE_LOCAL Local"
        MSG+=$'\n'"Timezone: $TZ (UTC$OFFSET)"
        MSG+=$'\n'"User: $USER@$HOST"
        git commit -m "$MSG"
    else
        git commit -m "$DEFAULT_MSG"$'\n\n'"UTC: $DATE_UTC | User: $USER@$HOST"
    fi
    
    git push origin "$BRANCH"
    echo -e "${GREEN}✓ Update completed${NC}"
else
    echo "No changes to commit"
fi