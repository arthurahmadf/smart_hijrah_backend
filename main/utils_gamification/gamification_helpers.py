# main/utils/gamification_helpers.py
from django.utils import timezone
from datetime import timedelta, date
from main.models_gamification import UserLevel, UserStreak, AmalanCheckin
from main.models import PrayerNotificationLog
from main.utils_gamification.gamification_constants import (
    AMALAN_POINTS, LEVEL_THRESHOLDS, PRAYER_POINTS
)


def get_or_create_user_level(user):
    """Dapatkan atau buat UserLevel untuk user"""
    level, created = UserLevel.objects.get_or_create(user=user)
    if created:
        level.level = 'starter'
        level.total_points = 0
        level.save()
    return level


def update_user_points(user, points):
    """Update total poin user dan level"""
    level = get_or_create_user_level(user)
    level.total_points += points
    
    # Update level sesuai threshold
    new_level = 'starter'
    for lvl, threshold in LEVEL_THRESHOLDS.items():
        if level.total_points >= threshold:
            new_level = lvl
    level.level = new_level
    level.save()
    
    return level


def calculate_daily_prayer_points(user, target_date):
    """Hitung poin shalat wajib user pada tanggal tertentu"""
    logs = PrayerNotificationLog.objects.filter(
        user=user,
        date=target_date
    )
    return logs.count() * PRAYER_POINTS


def calculate_daily_amalan_points(user, target_date):
    """Hitung poin amalan user pada tanggal tertentu"""
    checkins = AmalanCheckin.objects.filter(
        user=user,
        date=target_date,
        status=True
    )
    total = 0
    for checkin in checkins:
        total += AMALAN_POINTS.get(checkin.amalan, 0)
    return total


def calculate_daily_total_points(user, target_date):
    """Hitung total poin user pada tanggal tertentu (shalat + amalan)"""
    prayer_points = calculate_daily_prayer_points(user, target_date)
    amalan_points = calculate_daily_amalan_points(user, target_date)
    return prayer_points + amalan_points


def get_today_checkins(user):
    """Dapatkan semua check-in amalan hari ini"""
    today = timezone.now().date()
    return AmalanCheckin.objects.filter(user=user, date=today)


def update_streak(user, amalan_name, target_date):
    """Update streak untuk amalan tertentu"""
    streak, created = UserStreak.objects.get_or_create(
        user=user,
        amalan=amalan_name
    )
    
    # Jika pertama kali atau belum ada check_date
    if not streak.last_check_date:
        streak.streak_count = 1
        streak.last_check_date = target_date
        streak.save()
        return streak
    
    # Cek selisih hari
    days_diff = (target_date - streak.last_check_date).days
    
    if days_diff == 1:
        # Berturut-turut, tambah streak
        streak.streak_count += 1
        streak.last_check_date = target_date
    elif days_diff == 0:
        # Sudah di-check hari ini, tidak berubah
        pass
    else:
        # Terlewat, reset streak
        streak.streak_count = 0
        streak.last_check_date = target_date
    
    streak.save()
    return streak