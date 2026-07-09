from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from main.models_tuntunan_shalat import TuntunanShalat, TuntunanShalatPage


class TuntunanShalatListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        items = (
            TuntunanShalat.objects
            .filter(is_active=True)
            .prefetch_related("pages")
        )

        data = [
            {
                "id": item.id,
                "order": item.order,
                "title": item.title,
                "page_count": item.pages.count(),
            }
            for item in items
        ]

        return Response({
            "success": True,
            "message": "OK",
            "data": data
        })


class TuntunanShalatReaderPageView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id, page_number):
        try:
            tuntunan = TuntunanShalat.objects.get(id=id, is_active=True)
        except TuntunanShalat.DoesNotExist:
            return Response({
                "success": False,
                "message": "Tuntunan shalat not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        pages_qs = TuntunanShalatPage.objects.filter(tuntunan=tuntunan)
        total_pages = pages_qs.count()

        try:
            page = pages_qs.get(page_number=page_number)
        except TuntunanShalatPage.DoesNotExist:
            return Response({
                "success": False,
                "message": "Page not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "message": "OK",
            "data": {
                "tuntunan_id": tuntunan.id,
                "page_number": page.page_number,
                "page_title": page.page_title,
                "total_pages": total_pages,
                "prev_page": page.page_number - 1 if page.page_number > 1 else None,
                "next_page": page.page_number + 1 if page.page_number < total_pages else None,
                "blocks": page.blocks,
            }
        })