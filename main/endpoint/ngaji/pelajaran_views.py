from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from main.models_ngaji import Pelajaran, DetailPelajaran, MateriPelajaran
from main.serializers.ngaji_serializers import (
    PelajaranSerializer, DetailPelajaranSerializer, MateriPelajaranSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_pelajaran(request):
    """Get all learning paths (pelajaran)"""
    try:
        pelajaran = Pelajaran.objects.all()
        serializer = PelajaranSerializer(pelajaran, many=True)
        
        return JsonResponse({
            "success": True,
            "message": "Pelajaran fetched successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_detail_pelajaran(request, pelajaran_id):
    """Get detail of a specific learning path (all steps)"""
    try:
        pelajaran = get_object_or_404(Pelajaran, id=pelajaran_id)
        details = DetailPelajaran.objects.filter(pelajaran=pelajaran)
        
        pelajaran_serializer = PelajaranSerializer(pelajaran)
        details_serializer = DetailPelajaranSerializer(details, many=True)
        
        return JsonResponse({
            "success": True,
            "message": "Detail pelajaran fetched successfully",
            "data": {
                "pelajaran": pelajaran_serializer.data,
                "steps": details_serializer.data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_materi_pelajaran(request, detail_pelajaran_id):
    """Get all learning materials for a specific lesson step"""
    try:
        detail = get_object_or_404(DetailPelajaran, id=detail_pelajaran_id)
        materi = MateriPelajaran.objects.filter(detail_pelajaran=detail)
        
        serializer = MateriPelajaranSerializer(materi, many=True)
        
        return JsonResponse({
            "success": True,
            "message": "Materi pelajaran fetched successfully",
            "data": {
                "id": detail.id,
                "title": detail.name,
                "description": detail.pelajaran.description,
                "lesson_material": serializer.data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request, detail_pelajaran_id):
    """Mark a lesson as finished"""
    try:
        detail = get_object_or_404(DetailPelajaran, id=detail_pelajaran_id)
        
        if not detail.is_finished:
            detail.is_finished = True
            detail.save()
            
            # Update parent pelajaran course_finished count
            pelajaran = detail.pelajaran
            pelajaran.course_finished = DetailPelajaran.objects.filter(
                pelajaran=pelajaran, is_finished=True
            ).count()
            pelajaran.save()
        
        return JsonResponse({
            "success": True,
            "message": "Progress updated successfully",
            "data": {
                "step_finished": detail.is_finished,
                "course_finished": pelajaran.course_finished,
                "course_total": pelajaran.course_total
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)