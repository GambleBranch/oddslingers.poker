"""
Tests for UserStats and UserBalance defensive creation fix.

These tests verify that the invariant "every user has UserStats/UserBalance 
for the current season" is maintained, even when rows are missing.

See: migration 0042_ensure_current_season_userstats_and_balance
"""
from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from oddslingers.models import UserStats, UserBalance

User = get_user_model()


class UserStatsDefensiveCreationTest(TestCase):
    """Test that userstats() and userbalance() handle missing rows gracefully"""

    def setUp(self):
        """Create a test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_userstats_creation_on_access(self):
        """Test that accessing userstats() creates missing row"""
        # Manually delete the UserStats row that was created during user creation
        UserStats.objects.filter(user=self.user).delete()
        
        # Verify the row doesn't exist
        self.assertFalse(
            UserStats.objects.filter(user=self.user).exists(),
            "UserStats should not exist initially"
        )
        
        # Accessing userstats() should create it
        stats = self.user.userstats()
        
        # Verify it was created
        self.assertIsNotNone(stats)
        self.assertEqual(stats.user, self.user)
        self.assertEqual(stats.hands_played, 0)
        self.assertGreater(stats.games_level, 0)
        
        # Verify it can be accessed again without issues
        stats2 = self.user.userstats()
        self.assertEqual(stats.id, stats2.id)

    def test_userbalance_creation_on_access(self):
        """Test that accessing userbalance() creates missing row"""
        # Manually delete the UserBalance row that was created during user creation
        UserBalance.objects.filter(user=self.user).delete()
        
        # Verify the row doesn't exist
        self.assertFalse(
            UserBalance.objects.filter(user=self.user).exists(),
            "UserBalance should not exist initially"
        )
        
        # Accessing userbalance() should create it
        balance = self.user.userbalance()
        
        # Verify it was created
        self.assertIsNotNone(balance)
        self.assertEqual(balance.user, self.user)
        self.assertEqual(balance.balance, Decimal(0))
        
        # Verify it can be accessed again without issues
        balance2 = self.user.userbalance()
        self.assertEqual(balance.id, balance2.id)

    def test_json_rendering_with_missing_stats(self):
        """Test that __json__() doesn't crash when UserStats is missing"""
        # Delete UserStats
        UserStats.objects.filter(user=self.user).delete()
        
        # This used to crash with "UserStats matching query does not exist"
        # but now should work
        user_json = self.user.__json__()
        
        # Verify the JSON contains expected fields
        self.assertIn('games_level', user_json)
        self.assertIn('cashtables_level', user_json)
        self.assertIn('tournaments_level', user_json)
        self.assertIsNotNone(user_json['games_level'])
        self.assertIsNotNone(user_json['cashtables_level'])
        self.assertIsNotNone(user_json['tournaments_level'])

    def test_json_rendering_with_missing_balance(self):
        """Test that __json__() doesn't crash when UserBalance is missing"""
        # Delete UserBalance
        UserBalance.objects.filter(user=self.user).delete()
        
        # This should work even with missing UserBalance
        user_json = self.user.__json__()
        self.assertIsNotNone(user_json)

    def test_both_stats_and_balance_missing(self):
        """Test handling when both UserStats and UserBalance are missing"""
        # Delete both rows
        UserStats.objects.filter(user=self.user).delete()
        UserBalance.objects.filter(user=self.user).delete()
        
        # Accessing both should work
        stats = self.user.userstats()
        balance = self.user.userbalance()
        
        self.assertIsNotNone(stats)
        self.assertIsNotNone(balance)
        
        # Verify __json__() also works
        user_json = self.user.__json__()
        self.assertIsNotNone(user_json)

    def test_cached_property_doesnt_break_with_missing_stats(self):
        """Test that cached_property games_level works with missing stats"""
        # Delete UserStats
        UserStats.objects.filter(user=self.user).delete()
        
        # Access games_level property (used in __json__())
        games_level = self.user.games_level
        
        # Should get a valid value
        self.assertGreater(games_level, 0)
        
        # And it should cache properly
        games_level2 = self.user.games_level
        self.assertEqual(games_level, games_level2)

    def test_new_user_creation_has_stats(self):
        """Test that newly created users automatically get UserStats/UserBalance"""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='newpass123'
        )
        
        # Verify UserStats exists
        self.assertTrue(
            UserStats.objects.filter(user=new_user).exists(),
            "New user should have UserStats created automatically"
        )
        
        # Verify UserBalance exists
        self.assertTrue(
            UserBalance.objects.filter(user=new_user).exists(),
            "New user should have UserBalance created automatically"
        )
