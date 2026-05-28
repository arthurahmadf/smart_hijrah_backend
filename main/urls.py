# main/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .endpoint.social import feed_views, story_views, comment_views, follow_views
from django.conf import settings
from django.conf.urls.static import static
from .endpoint.lifestyle import fest_views
from .endpoint import masjid_views
from .endpoint import klinik_views
from .endpoint.ngaji import kelas_views, pelajaran_views

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
    path('user/change_password/', views.change_password, name='change_password'),
    path('user/change_profile_picture/', views.change_profile_picture, name='change_profile_picture'),
    
    # SOCIAL FEEDS (TODAY) 
    path('feed/global/', feed_views.get_global_feed, name='get_global_feed'),
    path('feed/local/', feed_views.get_local_feed, name='get_local_feed'),
    path('feed/following/', feed_views.get_following_feed, name='get_following_feed'),

    path('feed/create/', feed_views.create_feed, name='create_feed'),
    path('feed/like/<int:feed_id>/', feed_views.like_feed, name='like_feed'),
    path('feed/search/', feed_views.search_feed, name='search_feed'),
    
    # STORIES 
    path('stories/global/', story_views.get_global_stories, name='get_global_stories'),
    path('stories/local/', story_views.get_local_stories, name='get_local_stories'),
    path('stories/following/', story_views.get_following_stories, name='get_following_stories'),
    path('stories/create/', story_views.create_story, name='create_story'),  # Tambah ini

    path('stories/seen/<int:story_id>/', story_views.mark_story_seen, name='mark_story_seen'),

    # COMMENT ENDPOINTS
    path('feed/comment/<int:feed_id>/', comment_views.add_comment, name='add_comment'),
    path('feed/comment/delete/<int:comment_id>/', comment_views.delete_comment, name='delete_comment'),
    path('feed/comments/<int:feed_id>/', comment_views.get_comments, name='get_comments'),

    # FOLLOW ENDPOINTS
    path('follow/<int:user_id>/', follow_views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', follow_views.unfollow_user, name='unfollow_user'),
    path('followers/<int:user_id>/', follow_views.get_followers, name='get_followers'),
    path('following/<int:user_id>/', follow_views.get_following, name='get_following'),
    path('follow/check/<int:user_id>/', follow_views.check_follow_status, name='check_follow_status'), 


    # LIFESTYLE - FEST
    path('fest/', fest_views.get_fests, name='get_fests'),
    path('fest/<int:fest_id>/', fest_views.get_fest_detail, name='get_fest_detail'),
    path('fest/category/<str:category>/', fest_views.get_fests_by_category, name='get_fests_by_category'),

    # NEARBY MASJIDS & REVIEWS
    path('masjids/nearby/', masjid_views.nearby_masjids, name='nearby_masjids'),
    path('masjids/<str:place_id>/', masjid_views.masjid_detail, name='masjid_detail'),
    path('masjids/<str:place_id>/review/', masjid_views.create_masjid_review, name='create_masjid_review'),
    path('masjids/<str:place_id>/reviews/', masjid_views.get_masjid_reviews, name='get_masjid_reviews'),
    path('masjids/review/check/<str:place_id>/', masjid_views.check_user_review, name='check_user_review'),
    path('masjids/review/delete/<int:review_id>/', masjid_views.delete_masjid_review, name='delete_masjid_review'),

    path('kliniks/nearby/', klinik_views.nearby_kliniks, name='nearby_kliniks'),
    path('kliniks/<str:place_id>/', klinik_views.klinik_detail, name='klinik_detail'),
    path('kliniks/<str:place_id>/review/', klinik_views.create_klinik_review, name='create_klinik_review'),
    path('kliniks/<str:place_id>/reviews/', klinik_views.get_klinik_reviews, name='get_klinik_reviews'),
    path('kliniks/review/check/<str:place_id>/', klinik_views.check_user_klinik_review, name='check_user_klinik_review'),
    path('kliniks/review/delete/<int:review_id>/', klinik_views.delete_klinik_review, name='delete_klinik_review'),

    # BELAJAR NGAJI - KELAS TAHFIDZ
    path('ngaji/kelas/', kelas_views.get_all_kelas, name='get_all_kelas'),
    path('ngaji/kelas/cari/', kelas_views.cari_kelas, name='cari_kelas'),
    path('ngaji/kelas/<int:kelas_id>/', kelas_views.get_kelas_detail, name='get_kelas_detail'),
    path('ngaji/kelas/<int:kelas_id>/daftar/', kelas_views.daftar_kelas, name='daftar_kelas'),
    
    # BELAJAR NGAJI - PELAJARAN
    path('ngaji/pelajaran/', pelajaran_views.get_all_pelajaran, name='get_all_pelajaran'),
    path('ngaji/pelajaran/<int:pelajaran_id>/', pelajaran_views.get_detail_pelajaran, name='get_detail_pelajaran'),
    path('ngaji/pelajaran/materi/<int:detail_pelajaran_id>/', pelajaran_views.get_materi_pelajaran, name='get_materi_pelajaran'),
    path('ngaji/pelajaran/progress/<int:detail_pelajaran_id>/', pelajaran_views.update_progress, name='update_progress'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)