# main/google_auth_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
import json
import os

User = get_user_model()

class GoogleLoginView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            access_token = data.get('access_token')
            
            if not access_token:
                return Response({
                    'success': False,
                    'message': 'Access token tidak ditemukan'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Verifikasi ID token (bukan access token)
                # ID token biasanya didapat dari GoogleSignIn di Flutter
                # Untuk testing di Postman, kita perlu ID token, bukan access token
                
                # Opsi 1: Pakai access token ke tokeninfo (tidak dapat nama)
                import requests as http_requests
                token_response = http_requests.get(
                    f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}'
                )
                
                if token_response.status_code != 200:
                    return Response({
                        'success': False,
                        'message': 'Token tidak valid atau expired'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                user_info = token_response.json()
                email = user_info.get('email')
                sub = user_info.get('sub')
                
                # Nama tidak ada di tokeninfo, coba dari People API
                name = ''
                try:
                    people_response = http_requests.get(
                        'https://people.googleapis.com/v1/people/me?personFields=names',
                        headers={'Authorization': f'Bearer {access_token}'}
                    )
                    if people_response.status_code == 200:
                        people_data = people_response.json()
                        names = people_data.get('names', [])
                        if names:
                            name = names[0].get('displayName', '')
                except:
                    pass
                
                # Jika nama masih kosong, gunakan email sebagai fallback
                if not name:
                    name = email.split('@')[0]  # Ambil dari email
                
                user, created = User.objects.get_or_create(
                    username=f"google_{sub}",
                    defaults={
                        'email': email,
                        'nama': name,
                        'email_verified': True,
                    }
                )
                
                if user.email != email:
                    user.email = email
                if user.nama != name:
                    user.nama = name
                user.save()
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Token Google tidak valid: {str(e)}'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login berhasil',
                'data': {
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'nama': user.nama,
                    },
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)