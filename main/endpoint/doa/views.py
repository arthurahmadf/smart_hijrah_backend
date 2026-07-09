from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from main.models_doa import Doa, DoaBookmark


def build_absolute_media_url(request, file_field):
    if file_field:
        return request.build_absolute_uri(file_field.url)
    return None


class DoaListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None

        bookmarked_ids = set()
        if user:
            bookmarked_ids = set(
                DoaBookmark.objects
                .filter(user=user)
                .values_list("doa_id", flat=True)
            )

        doas = (
            Doa.objects
            .filter(is_active=True, category__is_active=True)
            .select_related("category")
        )

        data = [
            {
                "id": doa.id,
                "order": doa.order,
                "title": doa.title,
                "isBookmarked": doa.id in bookmarked_ids,
                "category": {
                    "id": doa.category.id,
                    "order": doa.category.order,
                    "title": doa.category.title,
                }
            }
            for doa in doas
        ]

        return Response({
            "success": True,
            "message": "OK",
            "data": data
        })


class DoaDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        user = request.user if request.user.is_authenticated else None

        try:
            doa = (
                Doa.objects
                .select_related("category")
                .prefetch_related("contents")
                .get(id=id, is_active=True, category__is_active=True)
            )
        except Doa.DoesNotExist:
            return Response({
                "success": False,
                "message": "Doa not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        is_bookmarked = False
        if user:
            is_bookmarked = DoaBookmark.objects.filter(
                user=user,
                doa=doa
            ).exists()

        contents = [
            {
                "id": content.id,
                "subTitle": content.sub_title,
                "description": content.description,
                "arabicText": content.arabic_text,
                "transliteration": content.transliteration,
                "translation": content.translation,
                "reference": content.reference,
            }
            for content in doa.contents.all()
        ]

        return Response({
            "success": True,
            "message": "OK",
            "data": {
                "id": doa.id,
                "pageTitle": doa.page_title,
                "heroImageUrl": build_absolute_media_url(request, doa.hero_image),
                "isBookmarked": is_bookmarked,
                "contents": contents,
            }
        })


class DoaBookmarkToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        is_bookmarked = request.data.get("isBookmarked")

        if not isinstance(is_bookmarked, bool):
            return Response({
                "success": False,
                "message": "isBookmarked must be boolean",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            doa = Doa.objects.get(id=id, is_active=True)
        except Doa.DoesNotExist:
            return Response({
                "success": False,
                "message": "Doa not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        if is_bookmarked:
            DoaBookmark.objects.get_or_create(user=request.user, doa=doa)
        else:
            DoaBookmark.objects.filter(user=request.user, doa=doa).delete()

        return Response({
            "success": True,
            "message": "Bookmark updated",
            "data": None
        })