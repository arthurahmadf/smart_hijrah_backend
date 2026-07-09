from django.core.paginator import Paginator

from main.models_islamic_book import IslamicBook
from main.serializers.islamic_book_serializer import IslamicBookSerializer


HOME_LIMIT = 100


def get_epustaka_home(request):
    """
    Homepage e-Pustaka
    """

    base_queryset = (
        IslamicBook.objects
        .filter(is_published=True)
        .select_related(
            "category",
            "author",
            "uploader",
        )
    )

    deals_queryset = (
        base_queryset
        .filter(discount__gt=0)
        .order_by("-created_at")[:HOME_LIMIT]
    )

    free_queryset = (
        base_queryset
        .filter(price=0)
        .order_by("-created_at")[:HOME_LIMIT]
    )

    recommended_queryset = (
        base_queryset
        .filter(is_recommended=True)
        .order_by("-sold_count", "-created_at")[:HOME_LIMIT]
    )

    return {
        "total_book_available": base_queryset.count(),
        "owned_book_count": 0,  # V1
        "book_deals": IslamicBookSerializer(
            deals_queryset,
            many=True,
            context={"request": request},
        ).data,
        "free_books": IslamicBookSerializer(
            free_queryset,
            many=True,
            context={"request": request},
        ).data,
        "recommended_books": IslamicBookSerializer(
            recommended_queryset,
            many=True,
            context={"request": request},
        ).data,
    }


def get_all_books(
    request,
    filter_type,
    page=1,
    page_size=10,
):
    """
    Halaman 'Lihat Semua'
    """

    queryset = (
        IslamicBook.objects
        .filter(is_published=True)
        .select_related(
            "category",
            "author",
            "uploader",
        )
        .order_by("-created_at")
    )

    if filter_type == "deals":
        queryset = queryset.filter(discount__gt=0)

    elif filter_type == "free":
        queryset = queryset.filter(price=0)

    elif filter_type == "recommended":
        queryset = queryset.filter(is_recommended=True)

    else:
        raise ValueError("Invalid filter.")

    paginator = Paginator(queryset, page_size)

    page_obj = paginator.get_page(page)

    return {
        "current_page": page_obj.number,
        "total_page": paginator.num_pages,
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
        "books": IslamicBookSerializer(
            page_obj,
            many=True,
            context={"request": request},
        ).data,
    }