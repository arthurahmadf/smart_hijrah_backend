from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from main.models_feed import Feed, FeedLike, FeedComment, Follow,FeedPicture
from main.serializers.feed_serializers import FeedSerializer
import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

from main.pagination_utils import paginate_queryset

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_feed(request):
    """Get feeds for user with pagination"""
    try:
        user = request.user
        
        # Get users that current user follows
        following_users = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        
        # Get feeds from followed users OR sponsored feeds
        feeds = Feed.objects.filter(
            Q(user_id__in=following_users) | Q(is_sponsored=True)
        ).select_related('user').prefetch_related('pictures')
        
        # Pagination
        paginated_data = paginate_queryset(request, feeds, page_size=10, items_key='feeds')
        
        # Serialize the feeds
        serializer = FeedSerializer(paginated_data['feeds'], many=True, context={'request': request})
        paginated_data['feeds'] = serializer.data
        
        return JsonResponse({
            "success": True,
            "message": "Feed fetched successfully",
            "data": paginated_data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_feed(request):
    """Create a new feed post with image upload (max 5 images)"""
    try:
        # Ambil data dari form-data
        caption = request.POST.get('caption', '')
        location = request.POST.get('location', '')
        
        # Handle multiple image uploads
        images = request.FILES.getlist('images')
        
        # Validasi maksimal 5 gambar
        if len(images) > 5:
            return JsonResponse({
                "success": False,
                "message": "Maximum 5 images per post"
            }, status=400)
        
        # Validasi minimal 1 gambar
        if len(images) == 0:
            return JsonResponse({
                "success": False,
                "message": "At least 1 image is required"
            }, status=400)
        
        feed = Feed.objects.create(
            user=request.user,
            caption=caption,
            location=location,
            permalink=f"feed_{uuid.uuid4()}"
        )
        
        # Save images
        for idx, image in enumerate(images):
            # Validasi tipe file
            if not image.content_type.startswith('image'):
                return JsonResponse({
                    "success": False,
                    "message": f"File {image.name} is not an image"
                }, status=400)
            
            file_extension = image.name.split('.')[-1]
            new_filename = f"feeds/{request.user.id}/{uuid.uuid4()}.{file_extension}"
            saved_path = default_storage.save(new_filename, ContentFile(image.read()))
            image_url = request.build_absolute_uri(default_storage.url(saved_path))
            
            FeedPicture.objects.create(
                feed=feed,
                image=image_url,
                order=idx
            )
        
        serializer = FeedSerializer(feed, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Feed created successfully",
            "data": serializer.data
        }, status=201)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

api_view(['POST'])
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
            # Unlike
            like.delete()
            feed.like_count -= 1
            feed.save()
            return JsonResponse({
                "success": True,
                "message": "Feed unliked",
                "is_liked": False,
                "like_count": feed.like_count
            }, status=200)
        else:
            # Like
            feed.like_count += 1
            feed.save()
            return JsonResponse({
                "success": True,
                "message": "Feed liked",
                "is_liked": True,
                "like_count": feed.like_count
            }, status=200)
            
    except Feed.DoesNotExist:
        return JsonResponse({"success": False, "message": "Feed not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_feed(request):
    """Search feeds by caption or location with pagination"""
    try:
        query = request.GET.get('q', '')
        
        if not query:
            return JsonResponse({
                "success": True,
                "message": "No search query provided",
                "data": {
                    "current_page": 1,
                    "total_page": 0,
                    "total_items": 0,
                    "feeds": []
                }
            }, status=200)
        
        feeds = Feed.objects.filter(
            Q(caption__icontains=query) | Q(location__icontains=query)
        ).select_related('user').prefetch_related('pictures')
        
        # Pagination
        paginated_data = paginate_queryset(request, feeds, page_size=10, items_key='feeds')
        
        serializer = FeedSerializer(paginated_data['feeds'], many=True, context={'request': request})
        paginated_data['feeds'] = serializer.data
        
        return JsonResponse({
            "success": True,
            "message": f"Search results for '{query}'",
            "data": paginated_data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)