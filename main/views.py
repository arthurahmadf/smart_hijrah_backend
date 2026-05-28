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
from .email_utils import send_verification_email


# Create your views here.
# FIREBASE OJOK DIGANTI BANG CEK PENAK LEK COPAS COPAS
from main.firebase import init_firebase
init_firebase()
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.safestring import mark_safe

@api_view(['GET'])
def verify_email(request, token):
    """Verify user email using token and show HTML page"""
    from .email_utils import verify_email_token
    
    success, message = verify_email_token(token)
    
    # HTML template for verification result
    if success:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Terverifikasi - Smart Hijrah</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #1a5f1a 0%, #0d3d0d 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 500px;
                    width: 100%;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    overflow: hidden;
                    animation: slideUp 0.5s ease-out;
                }}
                
                @keyframes slideUp {{
                    from {{
                        opacity: 0;
                        transform: translateY(30px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateY(0);
                    }}
                }}
                
                .header {{
                    background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
                    padding: 40px 20px;
                    text-align: center;
                }}
                
                .logo {{
                    font-size: 64px;
                    margin-bottom: 10px;
                }}
                
                .header h1 {{
                    color: white;
                    font-size: 28px;
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                
                .header p {{
                    color: rgba(255,255,255,0.9);
                    font-size: 14px;
                }}
                
                .content {{
                    padding: 40px 30px;
                    text-align: center;
                }}
                
                .success-icon {{
                    width: 80px;
                    height: 80px;
                    background: #4caf50;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 25px;
                    animation: scaleIn 0.5s ease-out 0.2s both;
                }}
                
                @keyframes scaleIn {{
                    from {{
                        opacity: 0;
                        transform: scale(0.5);
                    }}
                    to {{
                        opacity: 1;
                        transform: scale(1);
                    }}
                }}
                
                .success-icon svg {{
                    width: 45px;
                    height: 45px;
                    color: white;
                }}
                
                .content h2 {{
                    color: #1b5e20;
                    font-size: 24px;
                    margin-bottom: 15px;
                }}
                
                .content p {{
                    color: #555;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 10px;
                }}
                
                .message-box {{
                    background: #e8f5e9;
                    border-radius: 12px;
                    padding: 15px;
                    margin: 25px 0;
                    border-left: 4px solid #2e7d32;
                }}
                
                .message-box p {{
                    margin: 0;
                    color: #2e7d32;
                    font-size: 14px;
                }}
                
                .redirect-info {{
                    background: #f5f5f5;
                    border-radius: 12px;
                    padding: 15px;
                    margin-top: 20px;
                }}
                
                .redirect-info p {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}
                
                .countdown {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2e7d32;
                }}
                
                .btn {{
                    display: inline-block;
                    background: #2e7d32;
                    color: white;
                    text-decoration: none;
                    padding: 12px 30px;
                    border-radius: 25px;
                    font-weight: 500;
                    margin-top: 20px;
                    transition: all 0.3s;
                    border: none;
                    cursor: pointer;
                }}
                
                .btn:hover {{
                    background: #1b5e20;
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }}
                
                .footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #eee;
                }}
                
                .footer p {{
                    color: #999;
                    font-size: 12px;
                }}
                
                @media (max-width: 480px) {{
                    .content {{
                        padding: 30px 20px;
                    }}
                    
                    .content h2 {{
                        font-size: 20px;
                    }}
                    
                    .content p {{
                        font-size: 14px;
                    }}
                }}
            </style>
            <script>
                let countdown = 3;
                const countdownElement = document.getElementById('countdown');
                const redirectMessage = document.getElementById('redirect-message');
                
                function updateCountdown() {{
                    if (countdownElement) {{
                        countdownElement.textContent = countdown;
                    }}
                    if (countdown > 0) {{
                        countdown--;
                        setTimeout(updateCountdown, 1000);
                    }} else {{
                        // Redirect to Smart Hijrah app
                        window.location.href = "smarthijrah://verified";
                        // Fallback: try to redirect to App Store or Google Play after 1 second
                        setTimeout(function() {{
                            if (redirectMessage) {{
                                redirectMessage.innerHTML = 'Tidak dapat membuka aplikasi? <a href="https://play.google.com/store/apps/details?id=com.smarthijrah">Klik di sini</a> untuk download.';
                            }}
                        }}, 1000);
                    }}
                }}
                
                setTimeout(updateCountdown, 1000);
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🕌</div>
                    <h1>Smart Hijrah</h1>
                    <p>Aplikasi Belajar Islam Terpercaya</p>
                </div>
                <div class="content">
                    <div class="success-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <h2>Email Berhasil Diverifikasi!</h2>
                    <p>Selamat datang di <strong>Smart Hijrah</strong></p>
                    <div class="message-box">
                        <p>✨ Akun Anda telah aktif dan siap digunakan ✨</p>
                    </div>
                    <div class="redirect-info">
                        <p>Anda akan dialihkan ke aplikasi <strong>Smart Hijrah</strong> dalam</p>
                        <p class="countdown" id="countdown">3</p>
                        <p>detik</p>
                    </div>
                    <button class="btn" onclick="window.location.href='smarthijrah://verified'">Buka Aplikasi Sekarang</button>
                </div>
                <div class="footer">
                    <p id="redirect-message"></p>
                    <p>&copy; 2026 Smart Hijrah | Membantu Umat Muslim Mempelajari Islam</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verifikasi Gagal - Smart Hijrah</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #1a5f1a 0%, #0d3d0d 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 500px;
                    width: 100%;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    overflow: hidden;
                    animation: slideUp 0.5s ease-out;
                }}
                
                @keyframes slideUp {{
                    from {{
                        opacity: 0;
                        transform: translateY(30px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateY(0);
                    }}
                }}
                
                .header {{
                    background: linear-gradient(135deg, #c62828 0%, #8e0000 100%);
                    padding: 40px 20px;
                    text-align: center;
                }}
                
                .logo {{
                    font-size: 64px;
                    margin-bottom: 10px;
                }}
                
                .header h1 {{
                    color: white;
                    font-size: 28px;
                    font-weight: 600;
                }}
                
                .content {{
                    padding: 40px 30px;
                    text-align: center;
                }}
                
                .error-icon {{
                    width: 80px;
                    height: 80px;
                    background: #ef5350;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 25px;
                }}
                
                .error-icon svg {{
                    width: 45px;
                    height: 45px;
                    color: white;
                }}
                
                .content h2 {{
                    color: #c62828;
                    font-size: 24px;
                    margin-bottom: 15px;
                }}
                
                .content p {{
                    color: #555;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                
                .message-box {{
                    background: #ffebee;
                    border-radius: 12px;
                    padding: 15px;
                    margin: 25px 0;
                    border-left: 4px solid #c62828;
                }}
                
                .message-box p {{
                    margin: 0;
                    color: #c62828;
                }}
                
                .btn {{
                    display: inline-block;
                    background: #2e7d32;
                    color: white;
                    text-decoration: none;
                    padding: 12px 30px;
                    border-radius: 25px;
                    font-weight: 500;
                    margin-top: 20px;
                    transition: all 0.3s;
                }}
                
                .btn:hover {{
                    background: #1b5e20;
                    transform: translateY(-2px);
                }}
                
                .footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #eee;
                }}
                
                .footer p {{
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🕌</div>
                    <h1>Smart Hijrah</h1>
                </div>
                <div class="content">
                    <div class="error-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </div>
                    <h2>Verifikasi Gagal</h2>
                    <p>Maaf, terjadi kesalahan saat memverifikasi email Anda.</p>
                    <div class="message-box">
                        <p>{message}</p>
                    </div>
                    <button class="btn" onclick="window.location.href='smarthijrah://resend-verification'">Kirim Ulang Verifikasi</button>
                </div>
                <div class="footer">
                    <p>&copy; 2026 Smart Hijrah | Membantu Umat Muslim Mempelajari Islam</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return HttpResponse(html_content)

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
            username=data.get("username"),
            nama=data.get("nama"),
            email=data.get("email"),
            alamat=data.get("alamat"),
            telepon=data.get("telepon"),
            email_verified=False,  # default false
        )
        foto_profil_base64 = data.get("foto_profil")
        if foto_profil_base64:
            user.foto_profil = helper.base64_to_image_file(foto_profil_base64, "profil")
            
        user.set_password(data.get("password"))
        user.save()
        
        # Send verification email
        success, message = send_verification_email(user, request)
        
        if not success:
            # Email gagal, tapi user tetap dibuat
            return JsonResponse({
                "success": True,
                "id": user.id,
                "message": f"User berhasil dibuat, tapi {message}. Silakan minta ulang verifikasi nanti."
            }, status=200)
        
        return JsonResponse({
            "success": True,
            "id": user.id,
            "message": "User berhasil dibuat. Silakan cek email untuk verifikasi."
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
def resend_verification_email(request):
    """Resend verification email to user using email address"""
    from .email_utils import send_verification_email
    
    try:
        import json
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                "success": False,
                "message": "Email is required"
            }, status=400)
        
        from main.models import User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "User with this email not found"
            }, status=404)
        
        if user.email_verified:
            return JsonResponse({
                "success": False,
                "message": "Email already verified"
            }, status=400)
        
        success, message = send_verification_email(user, request)
        
        if success:
            return JsonResponse({
                "success": True,
                "message": "Verification email sent. Please check your inbox."
            }, status=200)
        else:
            return JsonResponse({
                "success": False,
                "message": message
            }, status=500)
            
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

@api_view(['GET','PATCH'])
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

