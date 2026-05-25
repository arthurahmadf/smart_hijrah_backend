from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from main.models_feed import Follow
from main.models import User
from main.serializers.feed_serializers import UserBasicSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    """Follow a user"""
    try:
        user_to_follow = get_object_or_404(User, id=user_id)
        
        if user_to_follow.id == request.user.id:
            return JsonResponse({
                "success": False,
                "message": "You cannot follow yourself"
            }, status=400)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if not created:
            return JsonResponse({
                "success": False,
                "message": "Already following this user"
            }, status=400)
        
        return JsonResponse({
            "success": True,
            "message": f"Now following {user_to_follow.username}"
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    """Unfollow a user"""
    try:
        user_to_unfollow = get_object_or_404(User, id=user_id)
        
        Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Unfollowed {user_to_unfollow.username}"
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_followers(request, user_id):
    """Get list of followers"""
    try:
        user = get_object_or_404(User, id=user_id)
        followers = Follow.objects.filter(following=user).select_related('follower')
        
        data = []
        for follow in followers:
            serializer = UserBasicSerializer(follow.follower, context={'request': request})
            data.append(serializer.data)
        
        return JsonResponse({
            "success": True,
            "data": data,
            "count": len(data)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request, user_id):
    """Get list of users that this user follows"""
    try:
        user = get_object_or_404(User, id=user_id)
        following = Follow.objects.filter(follower=user).select_related('following')
        
        data = []
        for follow in following:
            serializer = UserBasicSerializer(follow.following, context={'request': request})
            data.append(serializer.data)
        
        return JsonResponse({
            "success": True,
            "data": data,
            "count": len(data)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_follow_status(request, user_id):
    """Check if current user follows a specific user"""
    try:
        user_to_check = get_object_or_404(User, id=user_id)
        
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user_to_check
        ).exists()
        
        return JsonResponse({
            "success": True,
            "is_following": is_following
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)