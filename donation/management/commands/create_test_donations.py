from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from donation.models import Donation


class Command(BaseCommand):
    help = 'Create test donation data for testing the TotalDonationAPIView endpoint'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing donations before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Donation.objects.count()
            Donation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing donations'))

        now = timezone.now()
        
        # Sample wallet addresses
        wallet_addresses = [
            '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
            '0x1234567890123456789012345678901234567890',
            '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
            '0x9876543210987654321098765432109876543210',
            '0x5555555555555555555555555555555555555555',
        ]
        
        # Sample email addresses (some donations have emails, some don't)
        email_addresses = [
            'user1@example.com',
            'user2@example.com',
            'donor@test.com',
            None,
            'benefactor@donate.org',
            None,
        ]

        created_count = 0

        # Create donations for different time periods
        time_periods = [
            # Current week (last 7 days) - 15 donations
            {
                'start_days_ago': 0,
                'end_days_ago': 7,
                'count': 15,
                'dit_range': (100, 500),
                'usdt_range': (50, 250),
            },
            # Previous week (8-14 days ago) - 10 donations for comparison
            {
                'start_days_ago': 7,
                'end_days_ago': 14,
                'count': 10,
                'dit_range': (80, 400),
                'usdt_range': (40, 200),
            },
            # Current month (last 30 days) - 25 donations
            {
                'start_days_ago': 0,
                'end_days_ago': 30,
                'count': 25,
                'dit_range': (50, 600),
                'usdt_range': (25, 300),
            },
            # Previous month (31-60 days ago) - 18 donations
            {
                'start_days_ago': 30,
                'end_days_ago': 60,
                'count': 18,
                'dit_range': (60, 500),
                'usdt_range': (30, 250),
            },
            # Current year (last 365 days) - 50 donations
            {
                'start_days_ago': 0,
                'end_days_ago': 365,
                'count': 50,
                'dit_range': (20, 800),
                'usdt_range': (10, 400),
            },
            # Previous year (366-730 days ago) - 40 donations
            {
                'start_days_ago': 365,
                'end_days_ago': 730,
                'count': 40,
                'dit_range': (30, 700),
                'usdt_range': (15, 350),
            },
            # Custom period for testing (90-120 days ago)
            {
                'start_days_ago': 90,
                'end_days_ago': 120,
                'count': 12,
                'dit_range': (100, 450),
                'usdt_range': (50, 225),
            },
        ]

        for period in time_periods:
            for _ in range(period['count']):
                # Random date within the period
                days_ago = random.randint(period['start_days_ago'], period['end_days_ago'])
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                donated_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
                
                # Random amounts
                dit_amount = Decimal(str(round(random.uniform(*period['dit_range']), 6)))
                usdt_amount = Decimal(str(round(random.uniform(*period['usdt_range']), 6)))
                
                # Random wallet and email
                receiver_address = random.choice(wallet_addresses)
                email_address = random.choice(email_addresses)
                
                # Random dragon flags (20% chance of having dragon, 50% of those delivered)
                has_dragon = random.random() < 0.2
                dragon_delivered = has_dragon and random.random() < 0.5
                
                # Create donation with explicit donated_at time
                donation = Donation(
                    dit_amount=dit_amount,
                    usdt_amount=usdt_amount,
                    receiver_address=receiver_address,
                    email_address=email_address,
                    has_dragon=has_dragon,
                    dragon_delivered=dragon_delivered,
                )
                # Save first to get the auto_now_add field set
                donation.save()
                # Then update the donated_at to our desired time
                Donation.objects.filter(id=donation.id).update(donated_at=donated_at)
                
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} test donations'))
        
        # Show summary statistics
        self.stdout.write(self.style.SUCCESS('\n=== Summary Statistics ==='))
        
        total = Donation.objects.count()
        self.stdout.write(f'Total donations in database: {total}')
        
        # Last 7 days
        week_count = Donation.objects.filter(
            donated_at__gte=now - timedelta(days=7)
        ).count()
        self.stdout.write(f'Donations in last 7 days: {week_count}')
        
        # Last 30 days
        month_count = Donation.objects.filter(
            donated_at__gte=now - timedelta(days=30)
        ).count()
        self.stdout.write(f'Donations in last 30 days: {month_count}')
        
        # Last 365 days
        year_count = Donation.objects.filter(
            donated_at__gte=now - timedelta(days=365)
        ).count()
        self.stdout.write(f'Donations in last 365 days: {year_count}')
        
        self.stdout.write(self.style.SUCCESS('\nYou can now test the endpoint with:'))
        self.stdout.write('  - No period parameter (all time)')
        self.stdout.write('  - period=week')
        self.stdout.write('  - period=month')
        self.stdout.write('  - period=year')
        self.stdout.write('  - period=custom&start_date=2025-10-15&end_date=2025-11-15')
