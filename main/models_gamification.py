# main/models_gamification.py
from django.db import models
from django.conf import settings

class UserLevel(models.Model):
    """Menyimpan level dan total poin user"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='level')
    total_points = models.IntegerField(default=0)
    level = models.CharField(max_length=20, default='starter')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gamification_user_level'

    def __str__(self):
        return f"{self.user.username} - {self.level} ({self.total_points} pts)"

    def get_level_thresholds(self):
        """Return threshold poin untuk setiap level"""
        from main.utils.gamification_constants import LEVEL_THRESHOLDS
        return LEVEL_THRESHOLDS

    def get_current_level(self):
        """Tentukan level berdasarkan total_points"""
        from main.utils.gamification_constants import LEVEL_THRESHOLDS
        current = 'starter'
        for level, threshold in LEVEL_THRESHOLDS.items():
            if self.total_points >= threshold:
                current = level
        return current

    def get_next_level(self):
        """Return level selanjutnya dan required points"""
        from main.utils.gamification_constants import LEVEL_THRESHOLDS
        levels = list(LEVEL_THRESHOLDS.keys())
        for i, level in enumerate(levels):
            if self.total_points < LEVEL_THRESHOLDS[level]:
                return {
                    'next_level': level,
                    'required_points': LEVEL_THRESHOLDS[level] - self.total_points,
                    'threshold': LEVEL_THRESHOLDS[level]
                }
        return {
            'next_level': None,
            'required_points': 0,
            'threshold': LEVEL_THRESHOLDS[levels[-1]]
        }


class AmalanCheckin(models.Model):
    """Menyimpan check-in amalan harian user"""
    AMALAN_CHOICES = [
        ('tilawah', 'Tilawah'),
        ('dzikir', 'Dzikir'),
        ('puasa_sunnah', 'Puasa Sunnah'),
        ('sedekah', 'Sedekah'),
        ('tahajjud', 'Tahajjud'),
        ('dhuha', 'Dhuha'),
        ('kajian', 'Kajian'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amalan_checkins')
    amalan = models.CharField(max_length=20, choices=AMALAN_CHOICES)
    date = models.DateField(auto_now_add=True)
    status = models.BooleanField(default=True)  # True = done, False = cancelled
    points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gamification_amalan_checkin'
        unique_together = ('user', 'amalan', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.amalan} - {self.date}"


class UserStreak(models.Model):
    """Menyimpan streak per amalan user"""
    AMALAN_CHOICES = [
        ('shalat', 'Shalat'),
        ('tilawah', 'Tilawah'),
        ('dzikir', 'Dzikir'),
        ('puasa_sunnah', 'Puasa Sunnah'),
        ('sedekah', 'Sedekah'),
        ('tahajjud', 'Tahajjud'),
        ('dhuha', 'Dhuha'),
        ('kajian', 'Kajian'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='streaks')
    amalan = models.CharField(max_length=20, choices=AMALAN_CHOICES)
    streak_count = models.IntegerField(default=0)
    last_check_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gamification_user_streak'
        unique_together = ('user', 'amalan')

    def __str__(self):
        return f"{self.user.username} - {self.amalan} - {self.streak_count}"