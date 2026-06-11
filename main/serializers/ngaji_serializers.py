from rest_framework import serializers
from main.models_ngaji import *
from main.my_utils import generate_url

class KelasScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KelasSchedule
        fields = ['id', 'days', 'start_time', 'end_time', 'duration_in_seconds', 'enrolled_students']

class KelasTahfidzSerializer(serializers.ModelSerializer):
    banner = serializers.SerializerMethodField()
    schedules = KelasScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = KelasTahfidz
        fields = [
            'id', 'title', 'description', 'duration_in_seconds', 'banner',
            'price', 'is_dewasa', 'lecturer_id', 'lecturer_name', 
            'enroll_count', 'learning_materials', 'schedules'
        ]
    
    def get_banner(self, obj):
        return generate_url(obj.banner, self.context.get('request'))

class PelajaranSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pelajaran
        fields = ['id', 'name', 'description', 'step', 'course_total', 'course_finished']

class DetailPelajaranSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailPelajaran
        fields = ['id', 'name', 'step', 'arabic_text_icon', 'is_finished']

class MateriPelajaranSerializer(serializers.ModelSerializer):
    class Meta:
        model = MateriPelajaran
        fields = ['id', 'title', 'description', 'arabic', 'latin', 'audio_url', 'order']

class KelasEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KelasEnrollment
        fields = [
            'id', 'kelas', 'selected_schedule', 'nama_lengkap', 'jenis_kelamin',
            'usia_in_tahun', 'parent_name', 'parent_phone', 'address', 
            'ngaji_level', 'is_dewasa', 'is_private', 'enrollment_status',
            'enrolled_at'
        ]
        read_only_fields = ['user', 'enrollment_status', 'enrolled_at']


class KelasEnrollmentRequestSerializer(serializers.Serializer):
    """Serializer untuk request daftar kelas"""
    kelas_id = serializers.IntegerField()
    is_dewasa = serializers.BooleanField()
    is_private = serializers.BooleanField(default=False)
    selected_schedule_id = serializers.IntegerField(allow_null=True, required=False)
    
    nama_lengkap = serializers.CharField(max_length=255)
    jenis_kelamin = serializers.ChoiceField(choices=['laki-laki', 'perempuan'])
    usia_in_tahun = serializers.IntegerField(min_value=0, max_value=120)
    
    parent_name = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    parent_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    
    address = serializers.CharField()
    
    ngaji_level = serializers.IntegerField(min_value=1, max_value=4)
    
    def validate(self, data):
        # Validasi: jika is_dewasa = false, parent_name dan parent_phone wajib
        if not data.get('is_dewasa', True):
            if not data.get('parent_name'):
                raise serializers.ValidationError({
                    'parent_name': 'Parent name is required when is_dewasa is false'
                })
            if not data.get('parent_phone'):
                raise serializers.ValidationError({
                    'parent_phone': 'Parent phone is required when is_dewasa is false'
                })
        
        # Validasi: jika is_private = true, selected_schedule_id wajib
        if data.get('is_private', False) and not data.get('selected_schedule_id'):
            raise serializers.ValidationError({
                'selected_schedule_id': 'Schedule ID is required for private class'
            })
        
        return data