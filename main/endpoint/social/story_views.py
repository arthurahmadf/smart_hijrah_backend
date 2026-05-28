from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q
import uuid
from main.models_feed import Story, StorySeen, Follow
from main.serializers.feed_serializers import StorySerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_story(request):
    """Create a new story with image or video (max 10MB for video)"""
    try:
        media_file = request.FILES.get('media')
        user_country = request.POST.get('user_country', '')
        
        if not media_file:
            return JsonResponse({
                "success": False,
                "message": "Media file is required"
            }, status=400)
        
        content_type = media_file.content_type
        if content_type.startswith('image'):
            media_type = 'image'
        elif content_type.startswith('video'):
            media_type = 'video'
            if media_file.size > 10 * 1024 * 1024:
                return JsonResponse({
                    "success": False,
                    "message": "Video file too large. Max 10MB"
                }, status=400)
        else:
            return JsonResponse({
                "success": False,
                "message": "File must be image or video"
            }, status=400)
        
        file_extension = media_file.name.split('.')[-1]
        new_filename = f"stories/{request.user.id}/{uuid.uuid4()}.{file_extension}"
        saved_path = default_storage.save(new_filename, ContentFile(media_file.read()))
        story_link = request.build_absolute_uri(default_storage.url(saved_path))
        
        expires_at = timezone.now() + timedelta(hours=24)
        
        story = Story.objects.create(
            user=request.user,
            story_link=story_link,
            user_country=user_country,
            isOnline=True,
            expires_at=expires_at
        )
        
        serializer = StorySerializer(story, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Story created successfully",
            "data": serializer.data
        }, status=201)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_global_stories(request):
    """Stories from users outside Indonesia"""
    try:
        now = timezone.now()
        
        stories = Story.objects.filter(
            expires_at__gt=now
        ).filter(
            ~Q(user_country__icontains='indonesia') | Q(user_country__isnull=True)
        ).select_related('user')
        
        serializer = StorySerializer(stories, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Global stories fetched successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_local_stories(request):
    """Stories from users in Indonesia"""
    try:
        now = timezone.now()
        
        stories = Story.objects.filter(
            expires_at__gt=now
        ).filter(
            user_country__icontains='indonesia'
        ).select_related('user')
        
        serializer = StorySerializer(stories, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Local stories fetched successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following_stories(request):
    """Stories from users that current user follows only"""
    try:
        user = request.user
        now = timezone.now()
        
        following_users = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        following_list = list(following_users)
        
        stories = Story.objects.filter(
            expires_at__gt=now
        ).filter(
            user_id__in=following_list
        ).select_related('user')
        
        serializer = StorySerializer(stories, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Following stories fetched successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_story_seen(request, story_id):
    """Mark a story as seen by current user"""
    try:
        story = Story.objects.get(id=story_id)
        
        seen, created = StorySeen.objects.get_or_create(
            user=request.user,
            story=story
        )
        
        return JsonResponse({
            "success": True,
            "message": "Story marked as seen"
        }, status=200)
        
    except Story.DoesNotExist:
        return JsonResponse({"success": False, "message": "Story not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)