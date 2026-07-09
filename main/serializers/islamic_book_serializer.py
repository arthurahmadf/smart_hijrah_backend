from rest_framework import serializers

from main.models_book_category import BookCategory
from main.models_book_author import BookAuthor
from main.models_islamic_book import IslamicBook


class BookCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCategory
        fields = [
            "id",
            "name",
        ]


class BookAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookAuthor
        fields = [
            "id",
            "name",
        ]


class IslamicBookSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    book_url = serializers.SerializerMethodField()
    category = serializers.CharField(source="category.name")
    author_name = serializers.CharField(source="author.name")
    uploader_name = serializers.SerializerMethodField()
    uploader_id = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    is_owned = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()

    class Meta:
        model = IslamicBook
        fields = [
            "id",
            "title",
            "cover_image_url",
            "category",
            "price",
            "discount",
            "publish_year",
            "author_name",
            "uploader_id",
            "uploader_name",
            "sold_count",
            "synopsis",
            "is_owned",
            "book_url",
            "created_at",
        ]

    def get_price(self, obj):
        return float(obj.price)


    def get_discount(self, obj):
        return float(obj.discount)

    def get_cover_image_url(self, obj):
        request = self.context.get("request")

        if not obj.cover:
            return ""

        if request:
            return request.build_absolute_uri(obj.cover.url)

        return obj.cover.url

    def get_book_url(self, obj):
        request = self.context.get("request")

        if not obj.pdf:
            return ""

        if request:
            return request.build_absolute_uri(obj.pdf.url)

        return obj.pdf.url

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

    def get_is_owned(self, obj):
        """
        V1:
        Belum ada sistem pembelian.
        """
        return False