from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from main.models_tuntunan_shalat import TuntunanShalat


def build_absolute_media_url(request, file_field):
    if file_field:
        return request.build_absolute_uri(file_field.url)
    return None


def content_to_blocks(content):
    blocks = []

    if not content:
        return blocks

    paragraphs = [
        paragraph.strip()
        for paragraph in content.split("\n\n")
        if paragraph.strip()
    ]

    for paragraph in paragraphs:
        blocks.append({
            "type": "paragraph",
            "text": paragraph
        })

    return blocks


class TuntunanShalatListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        items = TuntunanShalat.objects.filter(is_active=True)

        data = [
            {
                "id": item.id,
                "order": item.order,
                "title": item.title,
                "page_count": 1,
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
        if page_number != 1:
            return Response({
                "success": False,
                "message": "Page not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            tuntunan = TuntunanShalat.objects.get(id=id, is_active=True)
        except TuntunanShalat.DoesNotExist:
            return Response({
                "success": False,
                "message": "Tuntunan shalat not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        blocks = []

        hero_image_url = build_absolute_media_url(request, tuntunan.hero_image)
        if hero_image_url:
            blocks.append({
                "type": "image",
                "image_url": hero_image_url,
                "text": tuntunan.title
            })

        blocks.append({
            "type": "heading",
            "text": tuntunan.title
        })

        blocks.extend(content_to_blocks(tuntunan.content))

        return Response({
            "success": True,
            "message": "OK",
            "data": {
                "tuntunan_id": tuntunan.id,
                "page_number": 1,
                "page_title": tuntunan.title,
                "total_pages": 1,
                "prev_page": None,
                "next_page": None,
                "blocks": blocks,
            }
        })