from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, date
from main.models import UserPrayerPreference, PrayerNotificationLog, PrayerMonthDocument

import zoneinfo

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prayer_monitor(request):
    """
    Get user's prayer tracking status for today
    Status logic:
    - null: waktu sholat belum tiba
    - false: waktu sholat sudah terlewat tapi user belum check-in
    - true: user sudah check-in (sholat sudah dikerjakan)
    """
    try:
        user = request.user
        today = date.today()
        now = timezone.now()
        
        # Get user's prayer preferences
        prefs, created = UserPrayerPreference.objects.get_or_create(user=user)
        
        # Get today's prayer logs
        logs = PrayerNotificationLog.objects.filter(
            user=user,
            date=today
        ).values_list('prayer_name', flat=True)
        
        logs_list = list(logs)
        
        # Define prayer times (in local time)
        prayer_schedule = {
            'subuh': {'time': '04:30', 'is_passed': False},
            'dzuhur': {'time': '12:00', 'is_passed': False},
            'ashar': {'time': '15:30', 'is_passed': False},
            'maghrib': {'time': '18:00', 'is_passed': False},
            'isya': {'time': '19:30', 'is_passed': False},
        }
        
        # Get actual prayer times from database if available
        prayer_doc = PrayerMonthDocument.objects.filter(
            user=user,
            year=today.year,
            month=today.month
        ).first()
        
        if prayer_doc and prayer_doc.payload:
            payload = prayer_doc.payload
            for prayer in prayer_schedule.keys():
                if prayer in payload:
                    prayer_schedule[prayer]['time'] = payload[prayer]
        
        # Helper function to check if a prayer time has passed
        def is_prayer_time_passed(prayer_time_str, now_time):
            try:
                prayer_dt = datetime.strptime(prayer_time_str, '%H:%M').time()
                prayer_datetime = datetime.combine(today, prayer_dt)
                # Make timezone aware using Django's current timezone
                prayer_datetime = timezone.make_aware(prayer_datetime, timezone.get_current_timezone())
                return now_time > prayer_datetime
            except:
                return False
        
        # Evaluate each prayer
        prayer_status = {
            "user": user.id,
            "date": today.isoformat(),
            "subuh": None,
            "dzuhur": None,
            "ashar": None,
            "maghrib": None,
            "isya": None,
            "notification_preferences": {
                "subuh": prefs.subuh,
                "dzuhur": prefs.dzuhur,
                "ashar": prefs.ashar,
                "maghrib": prefs.maghrib,
                "isya": prefs.isya,
            }
        }
        
        for prayer in ['subuh', 'dzuhur', 'ashar', 'maghrib', 'isya']:
            if prayer in logs_list:
                prayer_status[prayer] = True
            else:
                prayer_time = prayer_schedule[prayer]['time']
                if is_prayer_time_passed(prayer_time, now):
                    prayer_status[prayer] = False
                else:
                    prayer_status[prayer] = None
        
        return JsonResponse({
            "success": True,
            "message": "Prayer monitor fetched successfully",
            "data": prayer_status
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_prayer_completed(request):
    """
    Mark a specific prayer as completed for today
    Body: {"prayer_name": "subuh"}
    """
    try:
        import json
        data = json.loads(request.body)
        prayer_name = data.get('prayer_name', '').lower()
        
        valid_prayers = ['subuh', 'dzuhur', 'ashar', 'maghrib', 'isya']
        if prayer_name not in valid_prayers:
            return JsonResponse({
                "success": False,
                "message": f"Invalid prayer name. Must be one of: {valid_prayers}"
            }, status=400)
        
        user = request.user
        today = date.today()
        
        # Check if already marked
        existing = PrayerNotificationLog.objects.filter(
            user=user,
            date=today,
            prayer_name=prayer_name
        ).first()
        
        if existing:
            return JsonResponse({
                "success": False,
                "message": f"{prayer_name} already marked as completed today"
            }, status=400)
        
        # Create log entry
        log = PrayerNotificationLog.objects.create(
            user=user,
            date=today,
            prayer_name=prayer_name
        )
        
        # Get updated status
        logs = PrayerNotificationLog.objects.filter(
            user=user,
            date=today
        ).values_list('prayer_name', flat=True)
        
        logs_list = list(logs)
        
        return JsonResponse({
            "success": True,
            "message": f"{prayer_name} marked as completed",
            "data": {
                "prayer": prayer_name,
                "date": today.isoformat(),
                "all_prayers": {
                    "subuh": "subuh" in logs_list,
                    "dzuhur": "dzuhur" in logs_list,
                    "ashar": "ashar" in logs_list,
                    "maghrib": "maghrib" in logs_list,
                    "isya": "isya" in logs_list,
                }
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prayer_history(request):
    """
    Get prayer history for a date range
    Query params: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
    """
    try:
        user = request.user
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not start_date_str or not end_date_str:
            return JsonResponse({
                "success": False,
                "message": "start_date and end_date are required"
            }, status=400)
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get logs within date range
        logs = PrayerNotificationLog.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Group by date
        history = {}
        for log in logs:
            date_str = log.date.isoformat()
            if date_str not in history:
                history[date_str] = {
                    "subuh": False,
                    "dzuhur": False,
                    "ashar": False,
                    "maghrib": False,
                    "isya": False
                }
            history[date_str][log.prayer_name] = True
        
        # Convert to list format
        result = []
        for date_str, prayers in history.items():
            result.append({
                "date": date_str,
                "prayers": prayers
            })
        
        return JsonResponse({
            "success": True,
            "message": "Prayer history fetched successfully",
            "data": {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "history": result
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prayer_statistics(request):
    """
    Get prayer statistics for current month
    """
    try:
        user = request.user
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        # Get all logs for current month
        logs = PrayerNotificationLog.objects.filter(
            user=user,
            date__year=current_year,
            date__month=current_month
        )
        
        # Count per prayer
        stats = {
            "subuh": 0,
            "dzuhur": 0,
            "ashar": 0,
            "maghrib": 0,
            "isya": 0,
            "total_days": 0,
            "perfect_days": 0
        }
        
        # Group by date
        days = {}
        for log in logs:
            date_str = log.date.isoformat()
            if date_str not in days:
                days[date_str] = []
            days[date_str].append(log.prayer_name)
            stats[log.prayer_name] += 1
        
        # Count total days and perfect days
        stats["total_days"] = len(days)
        
        for date_str, prayers in days.items():
            if len(prayers) == 5:  # All 5 prayers completed
                stats["perfect_days"] += 1
        
        # Calculate completion rate per prayer
        from calendar import monthrange
        total_days_in_month = monthrange(current_year, current_month)[1]
        days_so_far = today.day
        
        for prayer in ['subuh', 'dzuhur', 'ashar', 'maghrib', 'isya']:
            stats[f"{prayer}_rate"] = round((stats[prayer] / days_so_far) * 100, 1) if days_so_far > 0 else 0
        
        return JsonResponse({
            "success": True,
            "message": "Prayer statistics fetched successfully",
            "data": {
                "month": current_month,
                "year": current_year,
                "statistics": stats
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_notification_preferences(request):
    """
    Update user's notification preferences for prayers
    Body: {"subuh": true, "dzuhur": false, ...}
    """
    try:
        import json
        data = json.loads(request.body)
        user = request.user
        
        prefs, created = UserPrayerPreference.objects.get_or_create(user=user)
        
        valid_fields = ['subuh', 'dzuhur', 'ashar', 'maghrib', 'isya']
        updated = []
        
        for field in valid_fields:
            if field in data and isinstance(data[field], bool):
                setattr(prefs, field, data[field])
                updated.append(f"{field}={data[field]}")
        
        prefs.save()
        
        return JsonResponse({
            "success": True,
            "message": "Notification preferences updated successfully",
            "data": {
                "subuh": prefs.subuh,
                "dzuhur": prefs.dzuhur,
                "ashar": prefs.ashar,
                "maghrib": prefs.maghrib,
                "isya": prefs.isya,
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)