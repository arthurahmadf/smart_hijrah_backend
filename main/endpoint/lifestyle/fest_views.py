from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from main.models_fest import Fest
from main.serializers.fest_serializers import FestSerializer

from main.pagination_utils import paginate_queryset

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fests(request):
    """Get all fests with pagination"""
    try:
        # Get all fests (tanpa pagination untuk headlines & recommendations)
        headlines = Fest.objects.filter(is_headline=True)
        recommendations = Fest.objects.filter(is_recommendation=True)
        
        headlines_serializer = FestSerializer(headlines, many=True)
        recommendations_serializer = FestSerializer(recommendations, many=True)
        
        # All fests dengan pagination
        all_fests = Fest.objects.all()
        paginated_data = paginate_queryset(request, all_fests, page_size=10, items_key='all_fest')
        
        # Serialize
        fest_serializer = FestSerializer(paginated_data['all_fest'], many=True)
        paginated_data['all_fest'] = fest_serializer.data
        
        return JsonResponse({
            "success": True,
            "message": "Fests fetched successfully",
            "data": {
                "fest_headlines": headlines_serializer.data,
                "fest_recommendation": recommendations_serializer.data,
                "all_fest": paginated_data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fest_detail(request, fest_id):
    """Get detail of a specific fest"""
    try:
        fest = Fest.objects.get(id=fest_id)
        serializer = FestSerializer(fest)
        
        return JsonResponse({
            "success": True,
            "data": serializer.data
        }, status=200)
        
    except Fest.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Fest not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fests_by_category(request, category):
    """Get fests by category"""
    try:
        fests = Fest.objects.filter(category__iexact=category)
        serializer = FestSerializer(fests, many=True)
        
        return JsonResponse({
            "success": True,
            "data": serializer.data,
            "category": category,
            "count": len(serializer.data)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)