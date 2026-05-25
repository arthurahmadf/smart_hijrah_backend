# main/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .endpoint.social import feed_views, story_views, comment_views, follow_views
from django.conf import settings
from django.conf.urls.static import static
from .endpoint.lifestyle import fest_views
from .endpoint import masjid_views

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
    path('feed/', feed_views.get_user_feed, name='get_user_feed'),
    path('feed/create/', feed_views.create_feed, name='create_feed'),
    path('feed/like/<int:feed_id>/', feed_views.like_feed, name='like_feed'),
    path('feed/search/', feed_views.search_feed, name='search_feed'),
    
    # STORIES 
    path('stories/', story_views.get_stories, name='get_stories'),
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)