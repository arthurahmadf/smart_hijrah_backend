from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.db import transaction as pengatom
from django.db.models import Sum, Avg
from django.utils.timezone import now, timedelta
from django.utils import timezone
import json
from .models import *
from . import my_utils as helper
from firebase_admin import messaging, credentials

# Create your views here.
# FIREBASE OJOK DIGANTI BANG CEK PENAK LEK COPAS COPAS
from main.firebase import init_firebase
init_firebase()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscribe_notification(request):
    try:
        data = json.loads(request.body)
        token = data.get("token", None)
        if not token:
            return JsonResponse({"success":False,"message":"Token tidak boleh kosong"},status=400)
        user = request.user
        user.fcm_token = token
        user.save()
        return JsonResponse({"success":True,"message":"Token berhasil disimpan"}, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

def send_push(token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=token,
    )
    response = messaging.send(message)
    return response

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_prayer_month(request):
    try:
        user = request.user
        data = json.loads(request.body)

        year = data["year"]
        month = data["month"]
        source_hash = data["source_hash"]

        doc = PrayerMonthDocument.objects.filter(
            user=user,
            year=year,
            month=month
        ).first()

        if doc and doc.source_hash == source_hash:
            return JsonResponse({
                "success": True,
                "message": f"Data shalat gaperlu diupdate ({doc.source_hash})"
            })

        PrayerMonthDocument.objects.update_or_create(
            user=user,
            year=year,
            month=month,
            defaults={
                "location": data["location"],
                "timezone": data["timezone"],
                "source_hash": source_hash,
                "last_updated": data["last_updated"],
                "payload": data,
            }
        )

        return JsonResponse({
            "success": True,
            "message": "jadwal shalat synced suksesfoley"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_prayer_preferences(request):
    try:
        user = request.user
        data = json.loads(request.body)
        prefs, _ = UserPrayerPreference.objects.get_or_create(user=user)

        for field in ["subuh", "dzuhur", "ashar", "maghrib", "isya"]:
            if field in data and isinstance(data[field], bool):
                setattr(prefs, field, data[field])

        prefs.save()

        return JsonResponse({
            "success": True,
            "message": "alarm preference synced suksefoleyu",
            "data": {
                "subuh": prefs.subuh,
                "dzuhur": prefs.dzuhur,
                "ashar": prefs.ashar,
                "maghrib": prefs.maghrib,
                "isya": prefs.isya,
            }
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)


# USER --------------------------------------------------------------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_me(request):
    try:
        user = request.user
        user_data = {
            "id":user.id,
            "username":user.username,
            "name":user.nama,
            "email":user.email,
            "alamat":user.alamat,
            "profile_picture": helper.generate_url(user.foto_profil,request)
        }
        return JsonResponse({"success":True,"data":user_data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    
@api_view(['POST'])
def create_user(request):
    try:
        data = json.loads(request.body)
        user = User(
            username = data.get("username"),
            nama = data.get("nama"),
            email = data.get("email"),
            alamat = data.get("alamat"),
            telepon = data.get("telepon"),
        )
        foto_profil_base64 = data.get("foto_profil")
        if foto_profil_base64:
            user.foto_profil = helper.base64_to_image_file(foto_profil_base64,"profil")
            
        user.set_password(data.get("password"))
        user.save()
        return JsonResponse({"success": True, "id": user.id, "message": "User verhasil dibuat"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def change_profile_picture(request):
    try:
        data = json.loads(request.body)
        foto_base64 = data.get("foto_profil")

        if not foto_base64:
            return JsonResponse(
                {"success": False, "message": "Foto Profil tidak ditemukan"},
                status=400
            )

        user = request.user

        if user.foto_profil:
            user.foto_profil.delete(save=False)

        user.foto_profil = helper.base64_to_image_file(foto_base64, "profil")
        user.save()

        return JsonResponse(
            {"success": True, "message": "Foto Profil berhasil diubah"},
            status=200
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": str(e)},
            status=400
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def change_password(request):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
            user = get_object_or_404(User, id=data.get("user_id"))
            password = data.get("password")
            user.set_password(password)
            user.save()
            return JsonResponse({"success": True, "message": "Password updated"}, status=200)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

