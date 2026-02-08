from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Sync all blockchain data (distributions and claims)'

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
        self.stdout.write(self.style.MIGRATE_HEADING('=== Starting Blockchain Data Sync ==='))
        
        # Sync distributions
        self.stdout.write(self.style.MIGRATE_LABEL('\n[1/2] Syncing Reward Distributions'))
        call_command('sync_reward_distributions', 
                    from_block=options['from_block'],
                    to_block=options['to_block'])
        
        # Sync claims
        self.stdout.write(self.style.MIGRATE_LABEL('\n[2/2] Syncing User Claims'))
        call_command('sync_user_claims',
                    from_block=options['from_block'],
                    to_block=options['to_block'])
        
        self.stdout.write(self.style.SUCCESS('\n=== Blockchain Sync Completed ==='))
