from rest_framework import serializers
from main.models_healthy_tip import HealthyTip


class HealthyTipSerializer(serializers.ModelSerializer):
    banner_url = serializers.SerializerMethodField()
    uploader_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = HealthyTip
        fields = [
            "id",
            "title",
            "banner_url",
            "created_at",
            "description_short",
            "category",
            "article",
            "uploader_name",
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

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")