from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .services import (
    get_media_home,
    search_media,
    increment_short_view,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_media_islami(request):
    """
    Homepage Media Islami
    """

    try:
        short_page = int(request.GET.get("short_page", 1))
        short_page_size = int(request.GET.get("short_page_size", 10))

        article_page = int(request.GET.get("article_page", 1))
        article_page_size = int(request.GET.get("article_page_size", 10))

        data = get_media_home(
            request=request,
            short_page=short_page,
            short_page_size=short_page_size,
            article_page=article_page,
            article_page_size=article_page_size,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Media Islami fetched successfully",
                "data": data,
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=400,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_media_islami(request):
    """
    Search Media Islami
    """

    try:
        keyword = request.GET.get("q", "").strip()

        if not keyword:
            return JsonResponse(
                {
                    "success": True,
                    "message": "Search result",
                    "data": {
                        "popular_channel": [],
                        "shorts": {
                            "current_page": 1,
                            "total_page": 0,
                            "total_items": 0,
                            "items": [],
                        },
                        "artikel_islami": {
                            "current_page": 1,
                            "total_page": 0,
                            "total_items": 0,
                            "items": [],
                        },
                    },
                },
                status=200,
            )
        short_page = int(request.GET.get("short_page", 1))
        short_page_size = int(request.GET.get("short_page_size", 10))

        article_page = int(request.GET.get("article_page", 1))
        article_page_size = int(request.GET.get("article_page_size", 10))

        data = search_media(
            request=request,
            keyword=keyword,
            short_page=short_page,
            short_page_size=short_page_size,
            article_page=article_page,
            article_page_size=article_page_size,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Search media islami success",
                "data": data,
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=400,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def increase_short_view(request, short_id):
    """
    Increment view count
    """

    try:
        success = increment_short_view(short_id)

        if not success:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Short Islami not found",
                },
                status=404,
            )

        return JsonResponse(
            {
                "success": True,
                "message": "View count updated",
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=400,
        )