from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.utils import timezone
from main.models_kisah_nabi import KisahNabi, KisahNabiEpisode, KisahNabiReadLog
from main.serializers.kisah_nabi_serializers import KisahNabiSerializer, KisahNabiListSerializer
from main.pagination_utils import paginate_queryset
from django.core.paginator import Paginator

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_kisah_nabi(request):
    """Get all kisah nabi with pagination"""
    try:
        kisah_nabi = KisahNabi.objects.all()
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        paginator = Paginator(kisah_nabi, page_size)
        kisah_page = paginator.get_page(page)
        
        serializer = KisahNabiListSerializer(kisah_page, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Kisah Nabi fetched successfully",
            "data": {
                "current_page": kisah_page.number,
                "total_page": paginator.num_pages,
                "total_items": paginator.count,
                "kisah_nabi": serializer.data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_popular_kisah_nabi(request):
    """Get popular kisah nabi (most read)"""
    try:
        # Sort by total_read_count descending, limit to 10
        popular = KisahNabi.objects.all().order_by('-total_read_count')[:10]
        
        serializer = KisahNabiListSerializer(popular, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Popular Kisah Nabi fetched successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kisah_nabi_detail(request, kisah_id):
    """Get detail of a specific kisah nabi with all episodes"""
    try:
        kisah = get_object_or_404(KisahNabi, id=kisah_id)
        
        # Increment read count (optional, bisa juga di log)
        # KisahNabi.objects.filter(id=kisah_id).update(total_read_count=F('total_read_count') + 1)
        
        serializer = KisahNabiSerializer(kisah, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Kisah Nabi detail fetched successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def increment_read_count(request, kisah_id):
    """Increment read count when user reads a kisah nabi"""
    try:
        kisah = get_object_or_404(KisahNabi, id=kisah_id)
        
        # Increment total read count
        kisah.total_read_count = F('total_read_count') + 1
        kisah.save()
        
        # Refresh to get updated value
        kisah.refresh_from_db()
        
        # Log the read
        KisahNabiReadLog.objects.create(
            user=request.user,
            kisah_nabi=kisah
        )
        
        return JsonResponse({
            "success": True,
            "message": "Read count incremented successfully",
            "data": {
                "total_read_count": kisah.total_read_count
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def increment_episode_read_count(request, episode_id):
    """Increment read count when user reads a specific episode"""
    try:
        episode = get_object_or_404(KisahNabiEpisode, id=episode_id)
        kisah = episode.kisah_nabi
        
        # Increment total read count
        kisah.total_read_count = F('total_read_count') + 1
        kisah.save()
        kisah.refresh_from_db()
        
        # Log the read with episode
        KisahNabiReadLog.objects.create(
            user=request.user,
            kisah_nabi=kisah,
            episode=episode
        )
        
        return JsonResponse({
            "success": True,
            "message": "Episode read count incremented successfully",
            "data": {
                "total_read_count": kisah.total_read_count,
                "episode_id": episode.id
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)