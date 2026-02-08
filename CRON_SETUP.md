# DIT Rewards - Linux Cron Setup Guide

## Prerequisites

1. Ensure your Django project is deployed on Linux server
2. Python virtual environment is set up
3. All dependencies installed (including web3)

## Step 1: Make Script Executable

```bash
chmod +x scripts/sync_blockchain.sh
```

## Step 2: Test Manual Execution

```bash
# Test the script manually first
./scripts/sync_blockchain.sh

# Or test individual commands
python manage.py sync_reward_distributions
python manage.py sync_user_claims
python manage.py sync_all_blockchain_data
```

## Step 3: Edit Crontab

Open crontab editor:
```bash
crontab -e
```

## Step 4: Add Cron Jobs

### Option A: Every 5 Minutes (Recommended)
```cron
# Sync DIT Rewards blockchain data every 5 minutes
*/5 * * * * /path/to/your/project/scripts/sync_blockchain.sh >> /path/to/your/project/logs/cron.log 2>&1
```

### Option B: Every 10 Minutes
```cron
# Sync DIT Rewards blockchain data every 10 minutes
*/10 * * * * /path/to/your/project/scripts/sync_blockchain.sh >> /path/to/your/project/logs/cron.log 2>&1
```

### Option C: Every Hour
```cron
# Sync DIT Rewards blockchain data every hour
0 * * * * /path/to/your/project/scripts/sync_blockchain.sh >> /path/to/your/project/logs/cron.log 2>&1
```

### Option D: Multiple Times Per Day
```cron
# Sync at specific times: 00:00, 06:00, 12:00, 18:00
0 0,6,12,18 * * * /path/to/your/project/scripts/sync_blockchain.sh >> /path/to/your/project/logs/cron.log 2>&1
```

## Full Example Configuration

```cron
# DIT Rewards Blockchain Sync
# Runs every 5 minutes
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Main sync job
*/5 * * * * cd /home/user/DIT_admin && ./scripts/sync_blockchain.sh >> logs/cron.log 2>&1

# Alternative: Run commands directly without shell script
*/5 * * * * cd /home/user/DIT_admin && venv/bin/python manage.py sync_all_blockchain_data >> logs/sync.log 2>&1

# Log rotation (optional) - run daily at midnight
0 0 * * * find /home/user/DIT_admin/logs -name "*.log" -mtime +7 -delete
```

## Cron Time Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Examples:

```cron
# Every minute
* * * * * /path/to/script.sh

# Every 5 minutes
*/5 * * * * /path/to/script.sh

# Every 15 minutes
*/15 * * * * /path/to/script.sh

# Every hour at minute 0
0 * * * * /path/to/script.sh

# Every day at midnight
0 0 * * * /path/to/script.sh

# Every Monday at 3:30 AM
30 3 * * 1 /path/to/script.sh

# First day of every month at noon
0 12 1 * * /path/to/script.sh
```

## Step 5: Verify Cron Job

List all cron jobs:
```bash
crontab -l
```

Check if cron is running:
```bash
sudo systemctl status cron     # Ubuntu/Debian
sudo systemctl status crond    # CentOS/RHEL
```

## Step 6: Monitor Logs

```bash
# Watch live logs
tail -f logs/cron.log
tail -f logs/sync_distributions.log
tail -f logs/sync_claims.log

# Check recent sync activity
tail -n 50 logs/sync.log

# Search for errors
grep -i error logs/*.log
```

## Troubleshooting

### Cron job not running?

1. **Check cron service:**
   ```bash
   sudo systemctl status cron
   sudo systemctl restart cron
   ```

2. **Check system logs:**
   ```bash
   grep CRON /var/log/syslog          # Ubuntu/Debian
   grep CRON /var/log/cron            # CentOS/RHEL
   ```

3. **Verify paths:**
   - Use absolute paths in cron jobs
   - Ensure script has execute permissions
   - Check virtual environment path

4. **Environment variables:**
   Add to crontab if needed:
   ```cron
   SHELL=/bin/bash
   PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
   DJANGO_SETTINGS_MODULE=DIT_admin.settings
   ```

### Permission issues?

```bash
# Make script executable
chmod +x scripts/sync_blockchain.sh

# Ensure log directory exists and is writable
mkdir -p logs
chmod 755 logs
```

### Test with full paths:

```cron
*/5 * * * * /usr/bin/python3 /home/user/DIT_admin/manage.py sync_all_blockchain_data >> /home/user/DIT_admin/logs/sync.log 2>&1
```

## Alternative: Systemd Timer (Modern Linux)

### 1. Create service file:
```bash
sudo nano /etc/systemd/system/dit-rewards-sync.service
```

```ini
[Unit]
Description=DIT Rewards Blockchain Sync
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/DIT_admin
Environment="PATH=/path/to/DIT_admin/venv/bin"
ExecStart=/path/to/DIT_admin/venv/bin/python manage.py sync_all_blockchain_data
StandardOutput=append:/path/to/DIT_admin/logs/sync.log
StandardError=append:/path/to/DIT_admin/logs/sync.log
```

### 2. Create timer file:
```bash
sudo nano /etc/systemd/system/dit-rewards-sync.timer
```

```ini
[Unit]
Description=DIT Rewards Blockchain Sync Timer
Requires=dit-rewards-sync.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=dit-rewards-sync.service

[Install]
WantedBy=timers.target
```

### 3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dit-rewards-sync.timer
sudo systemctl start dit-rewards-sync.timer

# Check status
sudo systemctl status dit-rewards-sync.timer
sudo systemctl list-timers
```

## Best Practices

1. **Start with longer intervals** (10-15 minutes) and adjust based on needs
2. **Monitor RPC rate limits** - too frequent calls may hit API limits
3. **Set up log rotation** to prevent disk space issues
4. **Use absolute paths** in cron jobs
5. **Test manually** before adding to cron
6. **Monitor first runs** closely for errors
7. **Set up alerts** for sync failures (optional)

## Quick Setup Commands

```bash
# 1. Navigate to project
cd /path/to/DIT_admin

# 2. Make script executable
chmod +x scripts/sync_blockchain.sh

# 3. Test manually
./scripts/sync_blockchain.sh

# 4. Add to cron (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * cd $(pwd) && ./scripts/sync_blockchain.sh >> logs/cron.log 2>&1") | crontab -

# 5. Verify
crontab -l

# 6. Watch logs
tail -f logs/cron.log
```

## Email Notifications (Optional)

Add email to receive notifications:
```cron
MAILTO=your-email@example.com
*/5 * * * * /path/to/script.sh
```

Or use custom notification:
```bash
#!/bin/bash
./scripts/sync_blockchain.sh
if [ $? -ne 0 ]; then
    echo "Blockchain sync failed" | mail -s "DIT Sync Alert" admin@example.com
fi
```
