from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from main.models_ngaji import KelasTahfidz, KelasSchedule, KelasEnrollment
from main.serializers.ngaji_serializers import KelasTahfidzSerializer, KelasEnrollmentSerializer, KelasEnrollmentRequestSerializer
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def daftar_kelas(request, kelas_id):
    """
    Enroll user to a class with complete registration data
    
    Request body:
    {
        "kelas_id": 1,
        "is_dewasa": true,
        "is_private": false,
        "selected_schedule_id": 1,
        "nama_lengkap": "string",
        "jenis_kelamin": "laki-laki | perempuan",
        "usia_in_tahun": 12,
        "parent_name": "string (required if is_dewasa=false)",
        "parent_phone": "string (required if is_dewasa=false)",
        "address": "string",
        "ngaji_level": 1
    }
    """
    try:
        # Validasi request body
        serializer = KelasEnrollmentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse({
                "success": False,
                "message": "Data pendaftaran tidak valid",
                "errors": serializer.errors
            }, status=400)
        
        data = serializer.validated_data
        
        # Validasi kelas_id dari URL dan request body harus sama
        if data['kelas_id'] != kelas_id:
            return JsonResponse({
                "success": False,
                "message": "Kelas ID mismatch"
            }, status=400)
        
        # Cek apakah kelas ada
        try:
            kelas = KelasTahfidz.objects.get(id=kelas_id)
        except KelasTahfidz.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Kelas tidak ditemukan"
            }, status=404)
        
        # Validasi schedule jika dipilih
        selected_schedule = None
        if data.get('selected_schedule_id'):
            try:
                selected_schedule = KelasSchedule.objects.get(
                    id=data['selected_schedule_id'],
                    kelas=kelas
                )
            except KelasSchedule.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": "Schedule tidak ditemukan untuk kelas ini"
                }, status=400)
        
        # Cek apakah user sudah terdaftar di kelas ini
        existing = KelasEnrollment.objects.filter(
            user=request.user,
            kelas=kelas
        ).first()
        
        if existing:
            return JsonResponse({
                "success": False,
                "message": f"Anda sudah terdaftar di kelas {kelas.title}",
                "data": {
                    "enrollment_id": existing.id,
                    "status": existing.enrollment_status
                }
            }, status=400)
        
        # Buat enrollment baru
        enrollment = KelasEnrollment.objects.create(
            user=request.user,
            kelas=kelas,
            selected_schedule=selected_schedule,
            nama_lengkap=data['nama_lengkap'],
            jenis_kelamin=data['jenis_kelamin'],
            usia_in_tahun=data['usia_in_tahun'],
            parent_name=data.get('parent_name'),
            parent_phone=data.get('parent_phone'),
            address=data['address'],
            ngaji_level=data['ngaji_level'],
            is_dewasa=data['is_dewasa'],
            is_private=data.get('is_private', False),
            enrollment_status='pending'
        )
        
        # Update enroll_count di kelas
        kelas.enroll_count = KelasEnrollment.objects.filter(kelas=kelas, enrollment_status='approved').count()
        kelas.save()
        
        # Response data
        response_data = {
            "id": enrollment.id,
            "kelas_id": kelas.id,
            "kelas_title": kelas.title,
            "selected_schedule_id": selected_schedule.id if selected_schedule else None,
            "is_dewasa": enrollment.is_dewasa,
            "is_private": enrollment.is_private,
            "enrollment_status": enrollment.enrollment_status,
            "nama_lengkap": enrollment.nama_lengkap,
            "jenis_kelamin": enrollment.jenis_kelamin,
            "usia_in_tahun": enrollment.usia_in_tahun,
            "address": enrollment.address,
            "ngaji_level": enrollment.ngaji_level,
            "enrolled_at": enrollment.enrolled_at,
        }
        
        # Tambahkan field orang tua jika is_dewasa = false
        if not enrollment.is_dewasa:
            response_data["parent_name"] = enrollment.parent_name
            response_data["parent_phone"] = enrollment.parent_phone
        
        return JsonResponse({
            "success": True,
            "message": f"Pendaftaran berhasil! Silakan tunggu konfirmasi dari admin.",
            "data": response_data
        }, status=201)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)