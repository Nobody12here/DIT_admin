# Diora Reward Distribution API

This Django app tracks DIT token rewards distributed through the smart contract and claimed by users.

## Features

- Track reward distributions by NFT type (RED, GREEN, BLUE, BLACK, DRAGON, FLAWLESS_DIAMOND)
- Track user reward claims
- Time-based filtering (week, month, 6 months, year, custom)
- Percentage change calculations comparing current vs previous periods
- Full REST API with Swagger documentation

## Models

### RewardDistribution
Stores blockchain events when rewards are distributed by NFT type.

**Fields:**
- `nft_type`: Type of NFT (RED, GREEN, BLUE, BLACK, DRAGON, FLAWLESS_DIAMOND)
- `total_amount`: Total DIT tokens distributed
- `per_wallet_amount`: Amount per wallet
- `wallet_count`: Number of wallets rewarded
- `transaction_hash`: Blockchain transaction hash (unique)
- `block_number`: Block number
- `distributed_at`: Distribution timestamp
- `created_at`: Record creation timestamp

### UserRewardClaim
Stores blockchain events when users claim their rewards.

**Fields:**
- `wallet_address`: User's wallet address
- `amount`: DIT tokens claimed
- `transaction_hash`: Blockchain transaction hash (unique)
- `block_number`: Block number
- `claimed_at`: Claim timestamp
- `created_at`: Record creation timestamp

## API Endpoints

Base URL: `/api/diora-rewards/`

### 1. List Reward Distributions
**GET** `/api/diora-rewards/distributions/`

Query parameters:
- `nft_type`: Filter by NFT type (RED, GREEN, BLUE, BLACK, DRAGON, FLAWLESS_DIAMOND)
- `page`: Page number
- `page_size`: Results per page (max 100)

**POST** `/api/diora-rewards/distributions/`
Create new distribution record (used by blockchain sync service)

---

### 2. List User Claims
**GET** `/api/diora-rewards/claims/`

Query parameters:
- `wallet_address`: Filter by wallet address
- `page`: Page number
- `page_size`: Results per page (max 100)

**POST** `/api/diora-rewards/claims/`
Create new claim record (used by blockchain sync service)

---

### 3. User Claims Detail
**GET** `/api/diora-rewards/claims/{wallet_address}/`

Get all claims for a specific wallet with total claimed amount.

Response:
```json
{
  "wallet_address": "0x1234...",
  "total_claimed": "5000.500000",
  "total_claims_count": 15,
  "claims": [...]
}
```

---

### 4. Total Rewards Analytics
**GET** `/api/diora-rewards/total/`

Get total rewards distributed with time filtering and percentage changes.

Query parameters:
- `period`: Time filter - `week`, `month`, `6months`, `year`, or `custom`
- `start_date`: Required for custom period (YYYY-MM-DD)
- `end_date`: Required for custom period (YYYY-MM-DD)

Response (with period):
```json
{
  "period": "month",
  "start_date": "2026-01-08",
  "end_date": "2026-02-07",
  "current_period": {
    "total_distributed": "100000.000000",
    "total_distributions": 50,
    "total_wallets_rewarded": 1500
  },
  "previous_period": {
    "total_distributed": "80000.000000",
    "total_distributions": 40,
    "total_wallets_rewarded": 1200
  },
  "percentage_change": {
    "total_distributed": 25.00,
    "total_distributions": 25.00,
    "total_wallets_rewarded": 25.00
  }
}
```

Response (without period - all time):
```json
{
  "total_distributed": "500000.000000",
  "total_distributions": 250,
  "total_wallets_rewarded": 7500
}
```

---

### 5. NFT Type Rewards Analytics
**GET** `/api/diora-rewards/nft-type/`

Get rewards for a specific NFT type with time filtering.

Query parameters (required):
- `nft_type`: NFT type - `RED`, `GREEN`, `BLUE`, `BLACK`, `DRAGON`, or `FLAWLESS_DIAMOND`

Query parameters (optional):
- `period`: Time filter - `week`, `month`, `6months`, `year`, or `custom`
- `start_date`: For custom period (YYYY-MM-DD)
- `end_date`: For custom period (YYYY-MM-DD)

Response (with period):
```json
{
  "nft_type": "DRAGON",
  "period": "month",
  "start_date": "2026-01-08",
  "end_date": "2026-02-07",
  "current_period": {
    "total_distributed": "50000.000000",
    "total_distributions": 10,
    "total_wallets_rewarded": 500
  },
  "previous_period": {
    "total_distributed": "40000.000000",
    "total_distributions": 8,
    "total_wallets_rewarded": 400
  },
  "percentage_change": {
    "total_distributed": 25.00,
    "total_distributions": 25.00,
    "total_wallets_rewarded": 25.00
  }
}
```

---

### 6. All NFT Types Rewards Breakdown
**GET** `/api/diora-rewards/all-nft-types/`

Get rewards breakdown for all NFT types with time filtering.

Query parameters:
- `period`: Time filter - `week`, `month`, `6months`, `year`, or `custom`
- `start_date`: For custom period (YYYY-MM-DD)
- `end_date`: For custom period (YYYY-MM-DD)

Response (with period):
```json
{
  "period": "month",
  "start_date": "2026-01-08",
  "end_date": "2026-02-07",
  "nft_types": {
    "RED": {
      "current_period": {...},
      "previous_period": {...},
      "percentage_change": {...}
    },
    "GREEN": {...},
    "BLUE": {...},
    "BLACK": {...},
    "DRAGON": {...},
    "FLAWLESS_DIAMOND": {...}
  }
}
```

## Setup

1. Add to INSTALLED_APPS in settings.py:
```python
INSTALLED_APPS = [
    ...
    'diora_reward',
]
```

2. Add to urls.py:
```python
urlpatterns = [
    ...
    path('api/diora-rewards/', include('diora_reward.urls')),
]
```

3. Run migrations:
```bash
python manage.py makemigrations diora_reward
python manage.py migrate
```

## Blockchain Integration

Data should be fetched from the smart contract events:

### RewardsDistributed Event
```solidity
event RewardsDistributed(
    NFTType indexed nftType,
    uint256 totalAmount,
    uint256 perWallet,
    uint256 walletCount
);
```

### RewardsClaimed Event
```solidity
event RewardsClaimed(address indexed user, uint256 amount);
```

Use a blockchain indexer or event listener to:
1. Listen to these events
2. POST data to the API endpoints
3. Store transaction hash, block number, and timestamp

## Admin Interface

Both models are registered in the Django admin with:
- List displays showing key information
- Filtering by date and NFT type
- Search by transaction hash and wallet address
- Read-only blockchain fields
- Date hierarchy for easy navigation

## Usage Examples

### Get rewards for last week
```bash
GET /api/diora-rewards/total/?period=week
```

### Get DRAGON NFT rewards for last month
```bash
GET /api/diora-rewards/nft-type/?nft_type=DRAGON&period=month
```

### Get custom date range
```bash
GET /api/diora-rewards/total/?period=custom&start_date=2026-01-01&end_date=2026-01-31
```

### Get user's claimed rewards
```bash
GET /api/diora-rewards/claims/0x1234567890abcdef/
```

### Get all NFT types breakdown for 6 months
```bash
GET /api/diora-rewards/all-nft-types/?period=6months
```

## Notes

- All amounts are stored with 6 decimal places for DIT token precision
- Transaction hashes must be unique (enforced at database level)
- Timestamps should be UTC from blockchain
- Percentage changes show increase/decrease compared to previous period
- API supports pagination for large datasets
