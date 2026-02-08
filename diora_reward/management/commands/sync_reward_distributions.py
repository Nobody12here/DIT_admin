from django.core.management.base import BaseCommand
from diora_reward.services.blockchain_service import DITRewardsBlockchainService
from diora_reward.models import RewardDistribution
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync reward distributions from blockchain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-block',
            type=int,
            default=None,
            help='Starting block number (default: last synced block + 1)'
        )
        parser.add_argument(
            '--to-block',
            type=str,
            default='latest',
            help='Ending block number or "latest"'
        )

    def handle(self, *args, **options):
        try:
            service = DITRewardsBlockchainService()
            
            # Get the last synced block if not specified
            if options['from_block'] is None:
                last_distribution = RewardDistribution.objects.order_by('-block_number').first()
                from_block = last_distribution.block_number + 1 if last_distribution else 0
                self.stdout.write(f'Last synced block: {from_block - 1}')
            else:
                from_block = options['from_block']
            
            to_block = options['to_block']
            
            self.stdout.write(f'Syncing from block {from_block} to {to_block}...')
            count = service.sync_reward_distributions(from_block, to_block)
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully synced {count} reward distributions'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
            logger.error(f'Error syncing reward distributions: {str(e)}')
            raise
