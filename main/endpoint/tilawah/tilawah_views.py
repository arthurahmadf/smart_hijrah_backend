import os
import uuid
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from main.models_tilawah import TilawahAyahPool, TilawahSession
from main.serializers.tilawah_serializers import TilawahAyahSerializer, TilawahSessionSerializer
from main.utils_tilawah.whisper_engine import transcribe_audio
from main.utils_tilawah.feedback_builder import build_feedback
from main.pagination_utils import paginate_queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_random_ayah(request):
    """
    GET /tilawah/ayah/random/?level=basic|intermediate|expert
    Return ayat random sesuai level
    """
    level = request.GET.get('level', 'basic')

    if level not in ['basic', 'intermediate', 'expert']:
        return Response(
            {'success': False, 'message': 'Level tidak valid. Gunakan basic, intermediate, atau expert.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Exclude ayat yang sudah pernah dibaca user (opsional, ambil random saja)
    ayahs = TilawahAyahPool.objects.filter(level=level)
    if not ayahs.exists():
        return Response(
            {'success': False, 'message': 'Tidak ada ayat untuk level ini.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Random satu ayat
    ayah = ayahs.order_by('?').first()
    serializer = TilawahAyahSerializer(ayah)

    return Response({
        'success': True,
        'message': 'Ayat berhasil diambil.',
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def submit_tilawah(request):
    """
    POST /tilawah/submit/
    Body (multipart/form-data):
        - audio: file (mp3/wav)
        - surah_number: int
        - ayah_number: int
        - level: str
    """
    # Validasi input
    audio_file = request.FILES.get('audio')
    surah_number = request.data.get('surah_number')
    ayah_number = request.data.get('ayah_number')
    level = request.data.get('level', 'basic')

    if not audio_file:
        return Response(
            {'success': False, 'message': 'File audio wajib diisi.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not surah_number or not ayah_number:
        return Response(
            {'success': False, 'message': 'surah_number dan ayah_number wajib diisi.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if level not in ['basic', 'intermediate', 'expert']:
        return Response(
            {'success': False, 'message': 'Level tidak valid.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Ambil ayat referensi dari database
    try:
        ayah_obj = TilawahAyahPool.objects.get(
            surah_number=int(surah_number),
            ayah_number=int(ayah_number)
        )
    except TilawahAyahPool.DoesNotExist:
        return Response(
            {'success': False, 'message': 'Ayat tidak ditemukan.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Validasi format audio
    allowed_formats = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-wav',
                       'audio/m4a', 'audio/x-m4a', 'video/webm', 'audio/webm']
    if audio_file.content_type not in allowed_formats:
        # Fallback cek ekstensi
        ext = os.path.splitext(audio_file.name)[1].lower()
        if ext not in ['.mp3', '.wav', '.m4a', '.webm']:
            return Response(
                {'success': False, 'message': 'Format audio tidak didukung. Gunakan mp3 atau wav.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Simpan audio sementara
    temp_filename = f"tilawah_temp_{uuid.uuid4().hex}{os.path.splitext(audio_file.name)[1]}"
    temp_path = os.path.join(settings.MEDIA_ROOT, 'tilawah_temp', temp_filename)
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)

    with open(temp_path, 'wb+') as f:
        for chunk in audio_file.chunks():
            f.write(chunk)

    try:
        # Transkripsi audio dengan Tarteel Whisper
        transcribe_result = transcribe_audio(temp_path)

        if not transcribe_result['success']:
            return Response(
                {'success': False, 'message': f'Gagal memproses audio: {transcribe_result["error"]}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        transcript = transcribe_result['transcript']

        # Build feedback
        feedback_result = build_feedback(
            ayah_text=ayah_obj.ayah_text,
            transcript=transcript,
            user_level=level
        )

        # Simpan session ke database
        session = TilawahSession.objects.create(
            user=request.user,
            surah_number=ayah_obj.surah_number,
            surah_name=ayah_obj.surah_name,
            ayah_number=ayah_obj.ayah_number,
            ayah_text=ayah_obj.ayah_text,
            level=level,
            tajwid_score=feedback_result['tajwid_score'],
            word_accuracy=feedback_result['word_accuracy'],
            transcript=transcript,
            feedback_data=feedback_result['ai_feedback'],
        )

        # Format response sesuai yang diharapkan frontend
        response_data = {
            'id': session.id,
            'id_str': f'tilawah_{session.id}',
            'surah_name': ayah_obj.surah_name,
            'ayah_number': ayah_obj.ayah_number,
            'ayah': ayah_obj.ayah_text,
            'audio_url': ayah_obj.audio_url,
            'tajwid_score': feedback_result['tajwid_score'],
            'makhraj_score': None,
            'makhraj_note': 'Penilaian makhraj belum tersedia pada versi ini.',
            'word_accuracy': feedback_result['word_accuracy'],
            'ai_feedback': feedback_result['ai_feedback'],
        }

        return Response({
            'success': True,
            'message': 'Tilawah berhasil diproses.',
            'data': response_data
        })

    finally:
        # Hapus file audio temporary
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_history(request):
    """
    GET /tilawah/history/?page=1&page_size=10
    Riwayat sesi tilawah user
    """
    sessions = TilawahSession.objects.filter(
        user=request.user
    ).order_by('-created_at')

    paginated = paginate_queryset(request, sessions, page_size=10, items_key='sessions')
    serializer = TilawahSessionSerializer(paginated['sessions'], many=True)
    paginated['sessions'] = serializer.data

    return Response({
        'success': True,
        'message': 'Riwayat tilawah berhasil diambil.',
        'data': paginated
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_detail(request, session_id):
    """
    GET /tilawah/session/<session_id>/
    Detail sesi tilawah
    """
    try:
        session = TilawahSession.objects.get(
            id=session_id,
            user=request.user
        )
    except TilawahSession.DoesNotExist:
        return Response(
            {'success': False, 'message': 'Sesi tidak ditemukan.'},
            status=status.HTTP_404_NOT_FOUND
        )

    response_data = {
        'id': session.id,
        'id_str': f'tilawah_{session.id}',
        'surah_name': session.surah_name,
        'ayah_number': session.ayah_number,
        'ayah': session.ayah_text,
        'level': session.level,
        'tajwid_score': session.tajwid_score,
        'makhraj_score': None,
        'makhraj_note': 'Penilaian makhraj belum tersedia pada versi ini.',
        'word_accuracy': session.word_accuracy,
        'ai_feedback': session.feedback_data,
        'created_at': session.created_at,
    }

    return Response({
        'success': True,
        'message': 'Detail sesi berhasil diambil.',
        'data': response_data
    })