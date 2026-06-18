# main/serializers/auth_serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        credential = attrs.get('username')
        password = attrs.get('password')
        
        if not credential or not password:
            raise serializers.ValidationError(
                "Username/email dan password wajib diisi.",
                code='authorization'
            )
        
        # Cari user berdasarkan username atau email
        try:
            user = User.objects.get(
                Q(username=credential) | Q(email=credential)
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Username/email atau password salah.",
                code='authorization'
            )
        
        # Cek password secara manual (karena authenticate sering bermasalah)
        if not user.check_password(password):
            raise serializers.ValidationError(
                "Username/email atau password salah.",
                code='authorization'
            )
        
        # Cek apakah user aktif
        if not user.is_active:
            raise serializers.ValidationError(
                "Akun tidak aktif.",
                code='inactive_account'
            )
        
        # Cek apakah email sudah terverifikasi
        if not user.email_verified:
            raise serializers.ValidationError(
                "Akun belum diverifikasi. Silakan cek email Anda untuk verifikasi.",
                code='email_not_verified'
            )
        
        # Set user ke attrs untuk diproses oleh parent
        attrs['username'] = user.username
        
        # Panggil parent validate dengan username yang sudah benar
        return super().validate(attrs)