from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import json
from main.models_feed import Story, StorySeen
from main.serializers.feed_serializers import StorySerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stories(request):
    """Get stories from users that current user follows"""
    try:
        user = request.user
        
        # Get users that current user follows
        from main.models_feed import Follow
        following_users = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        
        # Get active stories (not expired)
        now = timezone.now()
        stories = Story.objects.filter(
            user_id__in=following_users,
            expires_at__gt=now
        ).select_related('user')
        
        # Group by user
        stories_by_user = {}
        for story in stories:
            if story.user.id not in stories_by_user:
                stories_by_user[story.user.id] = []
            stories_by_user[story.user.id].append(story)
        
        # Serialize
        result = []
        for user_id, user_stories in stories_by_user.items():
            serializer = StorySerializer(user_stories, many=True, context={'request': request})
            result.extend(serializer.data)
        
        return JsonResponse({
            "success": True,
            "data": result
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_story(request):
    """Create a new story with video/image upload (max 15 sec for video)"""
    try:
        # Ambil file dari request.FILES
        media_file = request.FILES.get('media')
        
        if not media_file:
            return JsonResponse({
                "success": False,
                "message": "Media file is required"
            }, status=400)
        
        # Cek tipe file
        content_type = media_file.content_type
        if content_type.startswith('image'):
            media_type = 'image'
        elif content_type.startswith('video'):
            media_type = 'video'
            
            # Cek ukuran file max 10MB (estimasi video 15 detik)
            if media_file.size > 10 * 1024 * 1024:
                return JsonResponse({
                    "success": False,
                    "message": "Video file too large. Max 10MB for 15 seconds video"
                }, status=400)
        else:
            return JsonResponse({
                "success": False,
                "message": "File must be image or video"
            }, status=400)
        
        # Upload file
        file_extension = media_file.name.split('.')[-1]
        new_filename = f"stories/{request.user.id}/{uuid.uuid4()}.{file_extension}"
        saved_path = default_storage.save(new_filename, ContentFile(media_file.read()))
        
        # Buat URL publik
        media_url = request.build_absolute_uri(default_storage.url(saved_path))
        
        # Story expires in 24 hours
        expires_at = timezone.now() + timedelta(hours=24)
        
        story = Story.objects.create(
            user=request.user,
            media_url=media_url,
            media_type=media_type,
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