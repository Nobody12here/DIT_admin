# DIT Rewards Blockchain Sync - Quick Start

## Setup

### 1. Install Dependencies

```bash
pip install web3
```

### 2. Configure Environment Variables

Copy the example env file:
```bash
cp .env.example .env
```

Edit `.env` and set:
```bash
BLOCKCHAIN_RPC_URL=https://your-rpc-url.com
DIT_REWARDS_CONTRACT_ADDRESS=0xYourContractAddress
```

### 3. Run Migrations

```bash
python manage.py makemigrations diora_reward
python manage.py migrate
```

### 4. Test Connection

```bash
# Test manual sync
python manage.py sync_all_blockchain_data --from-block 0
```

## Management Commands

### Sync All Data
```bash
python manage.py sync_all_blockchain_data
```

### Sync Only Distributions
```bash
python manage.py sync_reward_distributions
```

### Sync Only Claims
```bash
python manage.py sync_user_claims
```

### With Options
```bash
# Sync from specific block
python manage.py sync_all_blockchain_data --from-block 1000000

# Sync specific block range
python manage.py sync_reward_distributions --from-block 1000000 --to-block 2000000

# Sync claims for specific wallet
python manage.py sync_user_claims --wallet 0x1234567890abcdef
```

## Setup Cron Job (Linux)

### Quick Setup
```bash
# Make script executable
chmod +x scripts/sync_blockchain.sh

# Add to crontab (runs every 5 minutes)
crontab -e
```

Add this line:
```cron
*/5 * * * * /path/to/DIT_admin/scripts/sync_blockchain.sh >> /path/to/DIT_admin/logs/cron.log 2>&1
```

See [CRON_SETUP.md](CRON_SETUP.md) for detailed instructions.

## API Endpoints

All endpoints are available at: `/api/diora-rewards/`

- `GET /api/diora-rewards/distributions/` - List all distributions
- `GET /api/diora-rewards/claims/` - List all claims
- `GET /api/diora-rewards/claims/{wallet}/` - Get claims for wallet
- `GET /api/diora-rewards/total/` - Total rewards with time filters
- `GET /api/diora-rewards/nft-type/` - Rewards by NFT type
- `GET /api/diora-rewards/all-nft-types/` - All NFT types breakdown

### Examples

```bash
# Get last week's total rewards
curl "http://localhost:8000/api/diora-rewards/total/?period=week"

# Get DRAGON NFT rewards for last month
curl "http://localhost:8000/api/diora-rewards/nft-type/?nft_type=DRAGON&period=month"

# Get user's claims
curl "http://localhost:8000/api/diora-rewards/claims/0x1234567890abcdef/"
```

## Monitoring

### Check Logs
```bash
tail -f logs/sync_distributions.log
tail -f logs/sync_claims.log
tail -f logs/cron.log
```

### Check Database
```bash
python manage.py shell
```

```python
from diora_reward.models import RewardDistribution, UserRewardClaim

# Check counts
print(f"Distributions: {RewardDistribution.objects.count()}")
print(f"Claims: {UserRewardClaim.objects.count()}")

# Check latest
print(RewardDistribution.objects.order_by('-distributed_at').first())
print(UserRewardClaim.objects.order_by('-claimed_at').first())
```

## Troubleshooting

### Connection Error
```
ConnectionError: Failed to connect to blockchain
```
**Solution:** Check `BLOCKCHAIN_RPC_URL` in settings/env file

### Module Not Found: web3
```
ModuleNotFoundError: No module named 'web3'
```
**Solution:** `pip install web3`

### Invalid Contract Address
```
ValueError: DIT_REWARDS_CONTRACT_ADDRESS not configured
```
**Solution:** Set `DIT_REWARDS_CONTRACT_ADDRESS` in .env file

### Cron Not Running
**Solution:** Check [CRON_SETUP.md](CRON_SETUP.md) troubleshooting section
