from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from main.models_ngaji import KelasTahfidz, KelasSchedule, KelasEnrollment
from main.serializers.ngaji_serializers import KelasTahfidzSerializer
import json
from django.db import models


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_kelas(request):
    """Get all kelas tahfidz with pagination"""
    try:
        kelas = KelasTahfidz.objects.all().prefetch_related('schedules')
        
        # Filter by is_dewasa if provided
        is_dewasa = request.GET.get('is_dewasa')
        if is_dewasa is not None:
            is_dewasa_bool = is_dewasa.lower() == 'true'
            kelas = kelas.filter(is_dewasa=is_dewasa_bool)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        paginator = Paginator(kelas, page_size)
        kelas_page = paginator.get_page(page)
        
        serializer = KelasTahfidzSerializer(kelas_page, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Kelas fetched successfully",
            "data": {
                "current_page": kelas_page.number,
                "total_page": paginator.num_pages,
                "total_items": paginator.count,
                "kelas": serializer.data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cari_kelas(request):
    """Search for classes by title or description"""
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        
        if not query:
            return JsonResponse({
                "success": False,
                "message": "Query parameter is required"
            }, status=400)
        
        kelas = KelasTahfidz.objects.filter(
            models.Q(title__icontains=query) | models.Q(description__icontains=query)
        ).prefetch_related('schedules')
        
        serializer = KelasTahfidzSerializer(kelas, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": f"Search results for '{query}'",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def daftar_kelas(request, kelas_id):
    """Enroll user to a class"""
    try:
        kelas = get_object_or_404(KelasTahfidz, id=kelas_id)
        
        # Check if already enrolled
        existing = KelasEnrollment.objects.filter(
            user=request.user,
            kelas=kelas
        ).first()
        
        if existing:
            return JsonResponse({
                "success": False,
                "message": "You are already enrolled in this class"
            }, status=400)
        
        # Create enrollment
        enrollment = KelasEnrollment.objects.create(
            user=request.user,
            kelas=kelas
        )
        
        # Update enroll count
        kelas.enroll_count = KelasEnrollment.objects.filter(kelas=kelas).count()
        kelas.save()
        
        return JsonResponse({
            "success": True,
            "message": f"Successfully enrolled in {kelas.title}",
            "data": {
                "kelas_id": kelas.id,
                "kelas_title": kelas.title,
                "enrolled_at": enrollment.enrolled_at
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kelas_detail(request, kelas_id):
    """Get detailed information about a specific class"""
    try:
        kelas = get_object_or_404(KelasTahfidz, id=kelas_id)
        
        # Check if user is enrolled
        is_enrolled = KelasEnrollment.objects.filter(
            user=request.user,
            kelas=kelas
        ).exists()
        
        serializer = KelasTahfidzSerializer(kelas, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Kelas detail fetched successfully",
            "data": {
                **serializer.data,
                "is_enrolled": is_enrolled
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)