from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from main.models_fest import Fest
from main.serializers.fest_serializers import FestSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fests(request):
    """Get all fests with headlines, recommendations, and all fests"""
    try:
        # Get headlines (is_headline=True)
        headlines = Fest.objects.filter(is_headline=True)
        headlines_serializer = FestSerializer(headlines, many=True)
        
        # Get recommendations (is_recommendation=True)
        recommendations = Fest.objects.filter(is_recommendation=True)
        recommendations_serializer = FestSerializer(recommendations, many=True)
        
        # Get all fests
        all_fests = Fest.objects.all()
        all_fests_serializer = FestSerializer(all_fests, many=True)
        
        return JsonResponse({
            "fest_headlines": headlines_serializer.data,
            "fest_recommendation": recommendations_serializer.data,
            "all_fest": all_fests_serializer.data
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