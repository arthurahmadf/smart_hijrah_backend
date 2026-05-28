import secrets
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.utils import timezone  # Tambahkan import ini di atas

def generate_verification_token(user):
    """Generate unique token for email verification"""
    raw_token = secrets.token_urlsafe(32)
    token = hashlib.sha256(f"{user.id}{raw_token}{user.email}".encode()).hexdigest()
    
    user.email_verification_token = token
    user.token_created_at = timezone.now()  # Ganti datetime.now() dengan timezone.now()
    user.save()
    
    return token

def send_verification_email(user, request):
    """Send verification email to user using Brevo SMTP"""
    try:
        token = generate_verification_token(user)
        
        # Build verification link
        verification_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': token})
        )
        
        # Email subject
        subject = "Verifikasi Email - Smart Hijrah"
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verifikasi Email</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #2e7d32;">Smart Hijrah</h2>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p>Assalamu'alaikum <strong>{user.nama or user.username}</strong>,</p>
                    <p>Terima kasih telah mendaftar di <strong>Smart Hijrah</strong>. Untuk melanjutkan, silakan verifikasi alamat email Anda dengan mengklik tombol di bawah ini:</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #2e7d32; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verifikasi Email
                    </a>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p>Atau copy link berikut ke browser Anda:</p>
                    <p style="background-color: #f5f5f5; padding: 10px; word-break: break-all; font-size: 12px;">
                        {verification_url}
                    </p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
                    <p>Link verifikasi ini akan kadaluarsa dalam {settings.VERIFICATION_TOKEN_EXPIRY_HOURS} jam.</p>
                    <p>Jika Anda tidak merasa mendaftar di Smart Hijrah, abaikan email ini.</p>
                    <hr>
                    <p>&copy; 2026 Smart Hijrah - Aplikasi Belajar Islam</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        plain_content = f"""
        Assalamu'alaikum {user.nama or user.username},
        
        Terima kasih telah mendaftar di Smart Hijrah. 
        
        Silakan verifikasi email Anda dengan mengunjungi link berikut:
        {verification_url}
        
        Link ini akan kadaluarsa dalam {settings.VERIFICATION_TOKEN_EXPIRY_HOURS} jam.
        
        Jika Anda tidak merasa mendaftar, abaikan email ini.
        
        -- 
        Smart Hijrah
        """
        
        # Send email using Django's send_mail
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=f"{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>",
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        return True, "Verification email sent"
        
    except Exception as e:
        return False, str(e)


def verify_email_token(token):
    """Verify email using token"""
    from main.models import User
    
    try:
        user = User.objects.get(email_verification_token=token)
        
        if user.token_created_at:
            # Gunakan timezone.now() yang aware, bukan datetime.now()
            if timezone.now() > user.token_created_at + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRY_HOURS):
                return False, "Verification link has expired"
        
        user.email_verified = True
        user.email_verification_token = None
        user.token_created_at = None
        user.save()
        
        return True, "Email verified successfully"
        
    except User.DoesNotExist:
        return False, "Invalid verification token"