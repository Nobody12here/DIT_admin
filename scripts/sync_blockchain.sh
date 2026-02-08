#!/bin/bash
# Sync blockchain data for DIT Rewards
# Location: /path/to/your/project/scripts/sync_blockchain.sh

# Change to project directory
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment (adjust path if needed)
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting blockchain sync..." >> logs/sync.log

# Sync reward distributions
python manage.py sync_reward_distributions >> logs/sync_distributions.log 2>&1
DIST_EXIT_CODE=$?

# Sync user claims
python manage.py sync_user_claims >> logs/sync_claims.log 2>&1
CLAIMS_EXIT_CODE=$?

# Log completion
if [ $DIST_EXIT_CODE -eq 0 ] && [ $CLAIMS_EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Sync completed successfully" >> logs/sync.log
else
    echo "[$TIMESTAMP] Sync completed with errors (dist: $DIST_EXIT_CODE, claims: $CLAIMS_EXIT_CODE)" >> logs/sync.log
fi
