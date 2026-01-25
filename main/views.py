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
import firebase_admin
from firebase_admin import messaging, credentials

# Create your views here.
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
            "jabatan":user.jabatan,
            
        }
        return JsonResponse({"success":True,"data":user_data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    
@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = User(
                username = data.get("username"),
                nama = data.get("nama"),
                email = data.get("email"),
                alamat = data.get("alamat"),
                telepon = data.get("telepon"),
            )
            user.set_password(data.get("password"))
            user.save()
            return JsonResponse({"success": True, "id": user.id, "message": "User verhasil dibuat"}, status=200)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid method"}, status=405)