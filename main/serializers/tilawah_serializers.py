from rest_framework import serializers
from main.models_tilawah import TilawahSession, TilawahAyahPool


class TilawahAyahSerializer(serializers.ModelSerializer):
    class Meta:
        model = TilawahAyahPool
        fields = ['surah_number', 'surah_name', 'ayah_number', 'ayah_text', 'audio_url', 'level']


class TilawahSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TilawahSession
        fields = [
            'id', 'surah_number', 'surah_name', 'ayah_number',
            'ayah_text', 'level', 'tajwid_score', 'word_accuracy',
            'feedback_data', 'created_at'
        ]