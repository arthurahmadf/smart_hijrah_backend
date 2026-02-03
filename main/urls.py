# main/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # NOTIFICATION
    path('notification/subscribe/', views.subscribe_notification, name='subscribe_token'),
    
    # AUTH --------------------------------------------------------------------------------------------------------------------------
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # JADWAL SHALAT
    path('jadwal_shalat/sync/', views.sync_prayer_month, name='sinkronisasi_jadwal_shalkat'),
    path('jadwal_shalat/notification_preference/', views.sync_prayer_preferences, name='sinkronisasi_preferensi_notifikasi'),
    
    # USER--------------------------------------------------------------------------------------------------------------------
    path('user/me/', views.users_me, name='users_me'),
    path('user/create/', views.create_user, name='create_user'),
]
