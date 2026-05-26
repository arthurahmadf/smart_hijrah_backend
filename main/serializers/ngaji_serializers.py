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