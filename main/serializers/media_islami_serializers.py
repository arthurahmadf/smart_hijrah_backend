from rest_framework import serializers

from main.models_media_category import MediaCategory
from main.models_short_islami import ShortIslami
from main.models_artikel_islami import ArtikelIslami


class MediaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaCategory
        fields = [
            "id",
            "name",
        ]


class ShortIslamiSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    short_url = serializers.SerializerMethodField()
    uploader_name = serializers.SerializerMethodField()
    uploader_id = serializers.SerializerMethodField()
    category = serializers.CharField(source="category.name")
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = ShortIslami
        fields = [
            "id",
            "title",
            "thumbnail_url",
            "short_url",
            "description",
            "created_at",
            "category",
            "view_count",
            "uploader_id",
            "uploader_name",
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")

        if not obj.thumbnail:
            return ""

        if request:
            return request.build_absolute_uri(obj.thumbnail.url)

        return obj.thumbnail.url

    def get_short_url(self, obj):
        request = self.context.get("request")

        if not obj.video:
            return ""

        if request:
            return request.build_absolute_uri(obj.video.url)

        return obj.video.url

    def get_uploader_name(self, obj):
        if not obj.uploader:
            return "Admin"

        full_name = obj.uploader.get_full_name()

        return full_name if full_name else obj.uploader.username

    def get_uploader_id(self, obj):
        if obj.uploader:
            return obj.uploader.id
        return None

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")


class ArtikelIslamiSerializer(serializers.ModelSerializer):
    banner_url = serializers.SerializerMethodField()
    uploader_name = serializers.SerializerMethodField()
    uploader_id = serializers.SerializerMethodField()
    category = serializers.CharField(source="category.name")
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = ArtikelIslami
        fields = [
            "id",
            "title",
            "banner_url",
            "description",
            "created_at",
            "category",
            "article",
            "uploader_name",
            "uploader_id",
        ]

    def get_banner_url(self, obj):
        request = self.context.get("request")

        if not obj.banner:
            return ""

        if request:
            return request.build_absolute_uri(obj.banner.url)

        return obj.banner.url

    def get_uploader_name(self, obj):
        if not obj.uploader:
            return "Admin"

        full_name = obj.uploader.get_full_name()

        return full_name if full_name else obj.uploader.username

    def get_uploader_id(self, obj):
        if obj.uploader:
            return obj.uploader.id
        return None

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")