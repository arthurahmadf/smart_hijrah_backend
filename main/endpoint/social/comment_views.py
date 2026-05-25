from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from main.models_feed import Feed, FeedComment
from main.serializers.feed_serializers import FeedCommentSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, feed_id):
    """Add comment to feed"""
    try:
        feed = get_object_or_404(Feed, id=feed_id)
        data = json.loads(request.body)
        text = data.get('text')
        
        if not text:
            return JsonResponse({
                "success": False,
                "message": "Comment text is required"
            }, status=400)
        
        comment = FeedComment.objects.create(
            user=request.user,
            feed=feed,
            text=text
        )
        
        # Update comment count
        feed.comment_count = FeedComment.objects.filter(feed=feed).count()
        feed.save()
        
        serializer = FeedCommentSerializer(comment, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Comment added",
            "data": serializer.data
        }, status=201)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """Delete comment"""
    try:
        comment = get_object_or_404(FeedComment, id=comment_id)
        
        # Only comment owner can delete
        if comment.user.id != request.user.id:
            return JsonResponse({
                "success": False,
                "message": "You can only delete your own comments"
            }, status=403)
        
        feed = comment.feed
        comment.delete()
        
        # Update comment count
        feed.comment_count = FeedComment.objects.filter(feed=feed).count()
        feed.save()
        
        return JsonResponse({
            "success": True,
            "message": "Comment deleted"
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comments(request, feed_id):
    """Get all comments for a feed"""
    try:
        feed = get_object_or_404(Feed, id=feed_id)
        comments = FeedComment.objects.filter(feed=feed).select_related('user')
        serializer = FeedCommentSerializer(comments, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)