from rest_framework import serializers

from main.models_tilawah import TilawahAyahPool, TilawahSession
from main.utils_tilawah.tajwid_v3.db_renderer import frontend_rules_from_ayah


# Mengikuti klasifikasi surah Makkiyah/Madaniyah yang umum digunakan.
# Semua surah selain nomor di bawah akan dianggap Makkiyah.
MADANIYAH_SURAH_NUMBERS = frozenset({
    2, 3, 4, 5, 8, 9, 13, 22, 24, 33,
    47, 48, 49, 55, 57, 58, 59, 60, 61,
    62, 63, 64, 65, 66, 76, 98, 99, 110,
})


LEVEL_RESPONSE_MAP = {
    "basic": "beginner",
    "intermediate": "intermediate",
    "expert": "expert",
}


class TilawahAyahSerializer(serializers.ModelSerializer):
    class Meta:
        model = TilawahAyahPool
        fields = [
            "surah_number",
            "surah_name",
            "ayah_number",
            "ayah_text",
            "audio_url",
            "level",
        ]


class TilawahSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TilawahSession
        fields = [
            "id",
            "surah_number",
            "surah_name",
            "ayah_number",
            "ayah_text",
            "level",
            "tajwid_score",
            "word_accuracy",
            "feedback_data",
            "created_at",
        ]


class TilawahSurahSerializer(serializers.Serializer):
    """
    Serializer untuk hasil agregasi daftar surah.

    Input serializer berbentuk dictionary dari queryset values/annotate,
    bukan instance model secara langsung.
    """

    surah_id = serializers.SerializerMethodField()
    surah_name = serializers.SerializerMethodField()
    total_ayah = serializers.IntegerField()

    def get_surah_id(self, obj):
        return str(obj["surah_number"])

    def get_surah_name(self, obj):
        # Untuk halaman pemilihan surah, tampilkan nama Indonesia/Latin.
        # Fallback ke surah_name jika data surah_name_id kosong.
        return (
            obj.get("surah_name")
            or obj.get("surah_name_id")
            or ""
        )


class TilawahSelectAyahSerializer(serializers.ModelSerializer):
    id_str = serializers.SerializerMethodField()
    surah_revelation = serializers.SerializerMethodField()
    surah_name = serializers.SerializerMethodField()
    surah_indo = serializers.SerializerMethodField()
    translation = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()
    transliteration = serializers.SerializerMethodField()
    rules = serializers.SerializerMethodField()

    class Meta:
        model = TilawahAyahPool
        fields = [
            "id",
            "id_str",
            "surah_revelation",
            "surah_name",
            "surah_indo",
            "surah_number",
            "ayah_number",
            "ayah_text",
            "translation",
            "transliteration",
            "audio_url",
            "level",
            "rules",
        ]

    def get_id_str(self, obj):
        return f"{obj.surah_number}-{obj.ayah_number}"

    def get_surah_revelation(self, obj):
        if obj.surah_number in MADANIYAH_SURAH_NUMBERS:
            return "Madaniyah"
        return "Makkiyah"

    def get_surah_name(self, obj):
        return obj.surah_name or ""

    def get_surah_indo(self, obj):
        return obj.surah_name_id or ""

    def get_translation(self, obj):
        return obj.ayah_translation or ""

    def get_audio_url(self, obj):
        return obj.audio_url or ""

    def get_transliteration(self, obj):
        return obj.ayah_transliteration or ""

    def get_rules(self, obj):
        return frontend_rules_from_ayah(obj)
