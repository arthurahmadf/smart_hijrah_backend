from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .services import (
    get_epustaka_home,
    get_all_books,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_epustaka(request):
    """
    Homepage e-Pustaka
    """

    try:

        data = get_epustaka_home(request)

        return JsonResponse(
            data,
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
def get_all_epustaka(request):
    """
    Lihat Semua Buku
    """

    try:

        filter_type = request.GET.get("filter", "recommended")

        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        data = get_all_books(
            request=request,
            filter_type=filter_type,
            page=page,
            page_size=page_size,
        )

        return JsonResponse(
            data,
            status=200,
        )

    except ValueError as e:

        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=400,
        )

    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=400,
        )