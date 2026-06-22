# main/endpoint/gamification_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta, date
import json

from main.models import User, PrayerNotificationLog
from main.models_gamification import UserLevel, AmalanCheckin, UserStreak
from main.serializers.gamification_serializers import (
    AmalanCheckinSerializer, StreakSerializer, LevelInfoSerializer
)
from main.utils_gamification.gamification_helpers import (
    get_or_create_user_level, update_user_points, update_streak,
    calculate_daily_total_points, get_today_checkins
)
from main.utils_gamification.gamification_constants import (
    AMALAN_POINTS, LEVEL_THRESHOLDS, PRAYER_POINTS
)


# ==================== 1. LEADERBOARD INFO ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard_info(request):
    """
    GET /leaderboard/info/
    Response: level info user termasuk rank
    """
    try:
        user = request.user
        level_obj = get_or_create_user_level(user)
        
        # Hitung rank user (total poin > user)
        rank = UserLevel.objects.filter(
            total_points__gt=level_obj.total_points
        ).count() + 1
        
        # Hitung required points to next level
        next_level = None
        required_points = 0
        for lvl, threshold in LEVEL_THRESHOLDS.items():
            if level_obj.total_points < threshold:
                next_level = lvl
                required_points = threshold - level_obj.total_points
                break
        
        # Cari semua user untuk leaderboard (top 50)
        leaderboard = UserLevel.objects.select_related('user').order_by('-total_points')[:50]
        
        data = {
            'user_id': user.id,
            'user_name': user.username,
            'user_profile': user.foto_profil.url if user.foto_profil else None,
            'rank': rank,
            'acquired_points': level_obj.total_points,
            'required_points_to_next_level': required_points if required_points > 0 else 0,
            'level': level_obj.level,
            'top_50': [
                {
                    'rank': idx + 1,
                    'user_name': ul.user.username,
                    'total_points': ul.total_points,
                    'level': ul.level
                }
                for idx, ul in enumerate(leaderboard)
            ]
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# ==================== 2. AMALAN CHECKIN ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def amalan_checkin(request):
    """
    POST /amalan/checkin/
    Body: {"amalan": "tilawah", "status": true/false}
    Idempotent: bisa dipanggil berkali-kali dengan status yang sama
    """
    try:
        data = json.loads(request.body)
        amalan = data.get('amalan')
        status = data.get('status')
        
        if not amalan:
            return JsonResponse({
                'success': False,
                'message': 'Amalan is required'
            }, status=400)
        
        if amalan not in AMALAN_POINTS:
            return JsonResponse({
                'success': False,
                'message': f'Invalid amalan: {amalan}'
            }, status=400)
        
        user = request.user
        today = timezone.now().date()
        
        # Cek apakah sudah check-in hari ini
        existing = AmalanCheckin.objects.filter(
            user=user,
            amalan=amalan,
            date=today
        ).first()
        
        if status:
            # Check-in (true)
            if existing:
                # Sudah check-in, return sukses
                total_today = calculate_daily_total_points(user, today)
                return JsonResponse({
                    'success': True,
                    'message': f'{amalan} already checked in today',
                    'data': {
                        'amalan': amalan,
                        'status': True,
                        'obtained_coins_today': total_today
                    }
                }, status=200)
            
            # Buat check-in baru
            points = AMALAN_POINTS[amalan]
            checkin = AmalanCheckin.objects.create(
                user=user,
                amalan=amalan,
                date=today,
                status=True,
                points_earned=points
            )
            
            # Tambah poin ke user level
            update_user_points(user, points)
            
            # Update streak
            streak_name = amalan
            update_streak(user, streak_name, today)
            
            # Hitung total poin hari ini
            total_today = calculate_daily_total_points(user, today)
            
            return JsonResponse({
                'success': True,
                'message': 'Check-in successful',
                'data': {
                    'amalan': amalan,
                    'status': True,
                    'obtained_coins_today': total_today
                }
            }, status=200)
            
        else:
            # Cancel check-in (false)
            if not existing:
                # Sudah false, return sukses
                total_today = calculate_daily_total_points(user, today)
                return JsonResponse({
                    'success': True,
                    'message': f'{amalan} already not checked in today',
                    'data': {
                        'amalan': amalan,
                        'status': False,
                        'obtained_coins_today': total_today
                    }
                }, status=200)
            
            # Hapus check-in
            points_to_remove = existing.points_earned
            existing.delete()
            
            # Kurangi poin dari user level
            level = get_or_create_user_level(user)
            level.total_points -= points_to_remove
            if level.total_points < 0:
                level.total_points = 0
            level.save()
            
            # Hitung total poin hari ini setelah cancel
            total_today = calculate_daily_total_points(user, today)
            
            return JsonResponse({
                'success': True,
                'message': 'Check-in cancelled',
                'data': {
                    'amalan': amalan,
                    'status': False,
                    'obtained_coins_today': total_today
                }
            }, status=200)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

# ==================== 3. JEJAK HIJRAH ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jejak_hijrah(request):
    """
    GET /jejak_hijrah/
    Response: Streak, monitor shalat, level info, check-in hari ini
    """
    try:
        user = request.user
        today = timezone.now().date()
        
        # 1. Hitung obtained coins today
        total_today = calculate_daily_total_points(user, today)
        
        # 2. Streak semua amalan (min 3 streak baru ditampilkan)
        streaks = UserStreak.objects.filter(user=user).exclude(streak_count__lt=3)
        streak_data = [
            {'name': s.amalan, 'streak_count': s.streak_count}
            for s in streaks
        ]
        
        # 3. Monitor shalat (dari spiritual tracker)
        logs = PrayerNotificationLog.objects.filter(user=user, date=today)
        logs_list = list(logs.values_list('prayer_name', flat=True))
        monitor_shalat = {
            'user': user.id,
            'date': today.isoformat(),
            'subuh': 'subuh' in logs_list,
            'dzuhur': 'dzuhur' in logs_list,
            'ashar': 'ashar' in logs_list,
            'maghrib': 'maghrib' in logs_list,
            'isya': 'isya' in logs_list,
        }
        
        # 4. Level info user
        level_obj = get_or_create_user_level(user)
        rank = UserLevel.objects.filter(
            total_points__gt=level_obj.total_points
        ).count() + 1
        
        required_points = 0
        for lvl, threshold in LEVEL_THRESHOLDS.items():
            if level_obj.total_points < threshold:
                required_points = threshold - level_obj.total_points
                break
        
        level_info = {
            'user_id': user.id,
            'user_name': user.username,
            'user_profile': user.foto_profil.url if user.foto_profil else None,
            'rank': rank,
            'acquired_points': level_obj.total_points,
            'required_points_to_next_level': required_points if required_points > 0 else 0,
            'level': level_obj.level,
        }
        
        # 5. Amalan check-in hari ini
        checkins_today = AmalanCheckin.objects.filter(user=user, date=today)
        checkin_data = [
            {'amalan': c.amalan, 'status': c.status}
            for c in checkins_today
        ]
        
        return JsonResponse({
            'success': True,
            'data': {
                'obtained_coins_today': total_today,
                'amalans_streak': streak_data,
                'monitor_shalat': monitor_shalat,
                'level_info': level_info,
                'amalan_checkin_today': checkin_data,
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)