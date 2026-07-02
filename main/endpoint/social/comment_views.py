from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from main.models_feed import Feed, FeedComment
from main.serializers.feed_serializers import FeedCommentSerializer

from main.pagination_utils import paginate_queryset

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, feed_id):
    """Add comment to feed (level 1)"""
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
        feed.comment_count = FeedComment.objects.filter(feed=feed, parent__isnull=True).count()
        feed.save()
        
        serializer = FeedCommentSerializer(comment, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Comment added",
            "data": serializer.data
        }, status=201)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reply_comment(request, comment_id):
    """
    Reply to a comment (always level 2)
    - If replying to level 1 → parent = level 1
    - If replying to level 2 → parent = level 1 (parent of the parent), replied_to = user of that comment
    """
    try:
        parent_comment = get_object_or_404(FeedComment, id=comment_id)
        data = json.loads(request.body)
        text = data.get('text')
        
        if not text:
            return JsonResponse({
                "success": False,
                "message": "Comment text is required"
            }, status=400)
        
        # Tentukan parent (selalu ke level 1)
        if parent_comment.parent is None:
            # Ini level 1 → parent-nya adalah comment ini
            parent = parent_comment
        else:
            # Ini level 2 → parent-nya adalah parent dari comment ini (level 1)
            parent = parent_comment.parent
        
        # User yang ditag (yang dibalas)
        replied_to = parent_comment.user
        
        # Buat reply (level 2)
        reply = FeedComment.objects.create(
            user=request.user,
            feed=parent_comment.feed,
            text=text,
            parent=parent,
            replied_to=replied_to
        )
        
        # Update comment count (hitung yang level 1)
        feed = parent_comment.feed
        feed.comment_count = FeedComment.objects.filter(feed=feed, parent__isnull=True).count()
        feed.save()
        
        serializer = FeedCommentSerializer(reply, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Reply added",
            "data": serializer.data
        }, status=201)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """Delete comment (and all its replies if level 1)"""
    try:
        comment = get_object_or_404(FeedComment, id=comment_id)
        
        if comment.user.id != request.user.id:
            return JsonResponse({
                "success": False,
                "message": "You can only delete your own comments"
            }, status=403)
        
        feed = comment.feed
        
        # Jika level 1, hapus semua reply-nya
        if comment.parent is None:
            comment.replies.all().delete()
        
        comment.delete()
        
        # Update comment count
        feed.comment_count = FeedComment.objects.filter(feed=feed, parent__isnull=True).count()
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
    """Get all level 1 comments for a feed (with nested replies)"""
    try:
        feed = get_object_or_404(Feed, id=feed_id)
        
        # Hanya ambil level 1 (parent is None)
        comments = FeedComment.objects.filter(
            feed=feed,
            parent__isnull=True
        ).select_related('user', 'replied_to').order_by('-created_at')
        
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        from django.core.paginator import Paginator
        paginator = Paginator(comments, page_size)
        comments_page = paginator.get_page(page)
        
        serializer = FeedCommentSerializer(comments_page, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Comments fetched successfully",
            "data": {
                "current_page": comments_page.number,
                "total_page": paginator.num_pages,
                "total_items": paginator.count,
                "comments": serializer.data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)