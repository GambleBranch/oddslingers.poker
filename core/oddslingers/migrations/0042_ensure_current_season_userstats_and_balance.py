# Generated manually to fix UserStats/UserBalance missing for current season

from django.db import migrations
from django.conf import settings


def ensure_current_season_stats(apps, schema_editor):
    """
    Ensure all existing users have UserStats and UserBalance rows for the 
    current season. This fixes the invariant violation where some users may
    be missing these rows (e.g., if prepare_new_season.py wasn't run after
    a season change).
    """
    User = apps.get_model('oddslingers', 'User')
    UserStats = apps.get_model('oddslingers', 'UserStats')
    UserBalance = apps.get_model('oddslingers', 'UserBalance')
    
    current_season = settings.CURRENT_SEASON
    
    # Create UserStats for any user missing it for current season
    for user in User.objects.all():
        stats, created = UserStats.objects.get_or_create(
            user=user,
            season=current_season,
            defaults={'hands_played': 0, 'games_level': 4000}
        )
        if created:
            print(f'Created UserStats for {user.username} (season {current_season})')
    
    # Create UserBalance for any user missing it for current season
    for user in User.objects.all():
        balance, created = UserBalance.objects.get_or_create(
            user=user,
            season=current_season,
            defaults={'balance': 0}
        )
        if created:
            print(f'Created UserBalance for {user.username} (season {current_season})')


def reverse_func(apps, schema_editor):
    """
    This migration should generally not be reversed in production.
    If reversed, it would delete the created UserStats/UserBalance rows.
    For safety, we leave this as a no-op.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('oddslingers', '0041_user_muck_after_winning'),
    ]

    operations = [
        migrations.RunPython(ensure_current_season_stats, reverse_func),
    ]
