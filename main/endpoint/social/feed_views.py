from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q
from django.shortcuts import get_object_or_404 
from main.models import User  
import uuid
import json
from main.models_feed import Feed, FeedLike, Follow
from main.serializers.feed_serializers import FeedSerializer


def insert_sponsored_feeds(feeds_list, sponsored_feeds, page_size=10):
    """Insert sponsored feeds at every 5th position"""
    result = []
    sponsored_index = 0
    feeds_index = 0
    
    while len(result) < page_size:
        if (len(result) + 1) % 5 == 0 and sponsored_index < len(sponsored_feeds):
            result.append(sponsored_feeds[sponsored_index])
            sponsored_index += 1
        elif feeds_index < len(feeds_list):
            result.append(feeds_list[feeds_index])
            feeds_index += 1
        else:
            break
    
    return result


import traceback
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_feed(request):
    """Create a new feed post with images (max 5)"""
    try:
        logger.debug("=== CREATE FEED START ===")
        logger.debug(f"User: {request.user.username}")
        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"FILES keys: {list(request.FILES.keys())}")
        
        feed_caption = request.POST.get('feed_caption', '')
        feed_location = request.POST.get('feed_location', '')
        user_country = request.POST.get('user_country', '')
        isSponsored = request.POST.get('isSponsored', 'false').lower() == 'true'
        
        images = request.FILES.getlist('images')
        logger.debug(f"Number of images: {len(images)}")
        
        if len(images) > 5:
            return JsonResponse({
                "success": False,
                "message": "Maximum 5 images per post"
            }, status=400)
        
        image_urls = []
        for idx, image in enumerate(images):
            logger.debug(f"Processing image {idx+1}: {image.name}")
            if not image.content_type.startswith('image'):
                logger.debug(f"Skipping non-image: {image.content_type}")
                continue
            
            file_extension = image.name.split('.')[-1]
            new_filename = f"feeds/{request.user.id}/{uuid.uuid4()}.{file_extension}"
            saved_path = default_storage.save(new_filename, ContentFile(image.read()))
            image_url = request.build_absolute_uri(default_storage.url(saved_path))
            image_urls.append(image_url)
            logger.debug(f"Image saved to: {saved_path}")
        
        feed = Feed.objects.create(
            user=request.user,
            feed_caption=feed_caption,
            feed_location=feed_location,
            feed_pictures=image_urls,
            user_country=user_country,
            isSponsored=isSponsored,
            permalink=f"feed_{uuid.uuid4()}"
        )
        logger.debug(f"Feed created with ID: {feed.id}")
        
        serializer = FeedSerializer(feed, context={'request': request})
        
        logger.debug("=== CREATE FEED SUCCESS ===")
        return JsonResponse({
            "success": True,
            "message": "Feed created successfully",
            "data": serializer.data
        }, status=201)
        
    except Exception as e:
        logger.error("=== CREATE FEED ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        
        return JsonResponse({
            "success": False, 
            "message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_global_feed(request):
    """Feed from users outside Indonesia"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        feeds = Feed.objects.filter(
            ~Q(user_country__icontains='indonesia') | Q(user_country__isnull=True)
        ).select_related('user').order_by('-created_at')
        
        sponsored_feeds = Feed.objects.filter(isSponsored=True).select_related('user')
        
        paginator = Paginator(feeds, page_size)
        feeds_page = paginator.get_page(page)
        
        feeds_serializer = FeedSerializer(list(feeds_page), many=True, context={'request': request})
        sponsored_serializer = FeedSerializer(list(sponsored_feeds), many=True, context={'request': request})
        
        mixed_feeds = insert_sponsored_feeds(feeds_serializer.data, sponsored_serializer.data, page_size)
        
        return JsonResponse({
            "success": True,
            "message": "Global feed fetched successfully",
            "data": {
                "current_page": page,
                "feeds": mixed_feeds
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_local_feed(request):
    """Feed from users in Indonesia"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        feeds = Feed.objects.filter(
            user_country__icontains='indonesia'
        ).select_related('user').order_by('-created_at')
        
        sponsored_feeds = Feed.objects.filter(isSponsored=True).select_related('user')
        
        paginator = Paginator(feeds, page_size)
        feeds_page = paginator.get_page(page)
        
        feeds_serializer = FeedSerializer(list(feeds_page), many=True, context={'request': request})
        sponsored_serializer = FeedSerializer(list(sponsored_feeds), many=True, context={'request': request})
        
        mixed_feeds = insert_sponsored_feeds(feeds_serializer.data, sponsored_serializer.data, page_size)
        
        return JsonResponse({
            "success": True,
            "message": "Local feed fetched successfully",
            "data": {
                "current_page": page,
                "feeds": mixed_feeds
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following_feed(request):
    """Feed from users that current user follows only"""
    try:
        user = request.user
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        following_users = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        following_list = list(following_users)
        
        feeds = Feed.objects.filter(
            user_id__in=following_list
        ).select_related('user').order_by('-created_at')
        
        sponsored_feeds = Feed.objects.filter(isSponsored=True).select_related('user')
        
        paginator = Paginator(feeds, page_size)
        feeds_page = paginator.get_page(page)
        
        feeds_serializer = FeedSerializer(list(feeds_page), many=True, context={'request': request})
        sponsored_serializer = FeedSerializer(list(sponsored_feeds), many=True, context={'request': request})
        
        mixed_feeds = insert_sponsored_feeds(feeds_serializer.data, sponsored_serializer.data, page_size)
        
        return JsonResponse({
            "success": True,
            "message": "Following feed fetched successfully",
            "data": {
                "current_page": page,
                "feeds": mixed_feeds
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_feed(request, feed_id):
    """Like or unlike a feed"""
    try:
        feed = Feed.objects.get(id=feed_id)
        
        like, created = FeedLike.objects.get_or_create(
            user=request.user,
            feed=feed
        )
        
        if not created:
            like.delete()
            feed.like_count -= 1
            feed.save()
            return JsonResponse({
                "success": True,
                "message": "Feed unliked",
                "isLiked": False,
                "like_count": feed.like_count
            }, status=200)
        else:
            feed.like_count += 1
            feed.save()
            return JsonResponse({
                "success": True,
                "message": "Feed liked",
                "isLiked": True,
                "like_count": feed.like_count
            }, status=200)
            
    except Feed.DoesNotExist:
        return JsonResponse({"success": False, "message": "Feed not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_feed(request):
    """Search feeds by caption or location"""
    try:
        query = request.GET.get('q', '')
        
        if not query:
            return JsonResponse({
                "success": True,
                "message": "No search query provided",
                "data": []
            }, status=200)
        
        feeds = Feed.objects.filter(
            Q(feed_caption__icontains=query) | Q(feed_location__icontains=query)
        ).select_related('user').order_by('-created_at')[:20]
        
        serializer = FeedSerializer(feeds, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": f"Search results for '{query}'",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_feeds(request, user_id):
    """
    Get all feeds from a specific user by user_id
    Response format sama persis dengan feed lainnya
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Cek apakah user yang diminta ada
        target_user = get_object_or_404(User, id=user_id)
        
        # Ambil feed dari user tersebut
        feeds = Feed.objects.filter(
            user=target_user
        ).select_related('user').order_by('-created_at')
        
        # Sponsored feeds (hanya yang dibuat oleh user tersebut)
        sponsored_feeds = feeds.filter(isSponsored=True)
        
        paginator = Paginator(feeds, page_size)
        feeds_page = paginator.get_page(page)
        
        feeds_serializer = FeedSerializer(list(feeds_page), many=True, context={'request': request})
        sponsored_serializer = FeedSerializer(list(sponsored_feeds), many=True, context={'request': request})
        
        mixed_feeds = insert_sponsored_feeds(feeds_serializer.data, sponsored_serializer.data, page_size)
        
        return JsonResponse({
            "success": True,
            "message": f"Feeds from {target_user.username} fetched successfully",
            "data": {
                "current_page": page,
                "feeds": mixed_feeds
            }
        }, status=200)
        
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)