from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings

from oddslingers.models import UserStats, UserBalance

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Diagnose and fix missing UserStats and UserBalance rows for users. '
        'Use --fix to automatically create missing rows for the current season.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            dest='fix',
            help='Automatically create missing UserStats and UserBalance rows',
        )
        parser.add_argument(
            '--season',
            type=int,
            default=settings.CURRENT_SEASON,
            help=f'Season number to check/fix (default: {settings.CURRENT_SEASON})',
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Check/fix specific user (username)',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        season = options['season']
        username = options['user']
        
        # Filter users if specified
        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" does not exist')
        else:
            users = User.objects.all()
        
        users_count = users.count() if hasattr(users, 'count') else len(users)
        self.stdout.write(f'Checking {users_count} user(s) for season {season}...')
        
        missing_stats = []
        missing_balance = []
        
        for user in users:
            # Check UserStats
            if not UserStats.objects.filter(user=user, season=season).exists():
                missing_stats.append(user)
                self.stdout.write(
                    self.style.WARNING(f'  ✗ {user.username}: Missing UserStats')
                )
            
            # Check UserBalance
            if not UserBalance.objects.filter(user=user, season=season).exists():
                missing_balance.append(user)
                self.stdout.write(
                    self.style.WARNING(f'  ✗ {user.username}: Missing UserBalance')
                )
        
        # Summary
        total_missing = len(set(missing_stats + missing_balance))
        self.stdout.write(
            f'\nFound {len(missing_stats)} users missing UserStats, '
            f'{len(missing_balance)} users missing UserBalance '
            f'({total_missing} users with issues)'
        )
        
        # Fix if requested
        if fix and total_missing > 0:
            if not self.confirm_fix(total_missing):
                self.stdout.write('Aborted.')
                return
            
            with transaction.atomic():
                # Create missing UserStats
                for user in missing_stats:
                    stats, created = UserStats.objects.get_or_create(
                        user=user,
                        season=season,
                        defaults={'hands_played': 0, 'games_level': 4000}
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created UserStats for {user.username}'
                        )
                    )
                
                # Create missing UserBalance
                for user in missing_balance:
                    balance, created = UserBalance.objects.get_or_create(
                        user=user,
                        season=season,
                        defaults={'balance': 0}
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created UserBalance for {user.username}'
                        )
                    )
            
            self.stdout.write(self.style.SUCCESS(f'\nFixed all {total_missing} user(s)'))
    
    def confirm_fix(self, count: int) -> bool:
        """Ask user to confirm before fixing"""
        response = input(
            f'This will create {count} missing rows. Continue? [y/N] '
        )
        return response.lower() == 'y'
