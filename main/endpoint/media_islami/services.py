from django.core.paginator import Paginator
from django.db.models import Q

from main.models_short_islami import ShortIslami
from main.models_artikel_islami import ArtikelIslami
from main.serializers.media_islami_serializers import (
    ShortIslamiSerializer,
    ArtikelIslamiSerializer,
)


def get_media_home(
    request,
    short_page=1,
    short_page_size=10,
    article_page=1,
    article_page_size=10,
):
    """
    Homepage Media Islami
    """

    short_queryset = (
        ShortIslami.objects
        .filter(is_published=True)
        .select_related("category", "uploader")
        .order_by("-created_at")
    )

    article_queryset = (
        ArtikelIslami.objects
        .filter(is_published=True)
        .select_related("category", "uploader")
        .order_by("-created_at")
    )

    short_paginator = Paginator(short_queryset, short_page_size)
    short_page_obj = short_paginator.get_page(short_page)

    article_paginator = Paginator(article_queryset, article_page_size)
    article_page_obj = article_paginator.get_page(article_page)

    return {
        "popular_channel": [],
        "shorts": {
            "current_page": short_page_obj.number,
            "total_page": short_paginator.num_pages,
            "total_items": short_paginator.count,
            "items": ShortIslamiSerializer(
                short_page_obj,
                many=True,
                context={"request": request},
            ).data,
        },
        "artikel_islami": {
            "current_page": article_page_obj.number,
            "total_page": article_paginator.num_pages,
            "total_items": article_paginator.count,
            "items": ArtikelIslamiSerializer(
                article_page_obj,
                many=True,
                context={"request": request},
            ).data,
        },
    }


def search_media(
    request,
    keyword,
    short_page=1,
    short_page_size=10,
    article_page=1,
    article_page_size=10,
):
    """
    Search Media Islami
    """

    keyword = keyword.strip()

    short_queryset = (
        ShortIslami.objects
        .filter(is_published=True)
        .filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(category__name__icontains=keyword)
        )
        .select_related("category", "uploader")
        .order_by("-created_at")
    )

    article_queryset = (
        ArtikelIslami.objects
        .filter(is_published=True)
        .filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(category__name__icontains=keyword)
        )
        .select_related("category", "uploader")
        .order_by("-created_at")
    )

    short_paginator = Paginator(short_queryset, short_page_size)
    short_page_obj = short_paginator.get_page(short_page)

    article_paginator = Paginator(article_queryset, article_page_size)
    article_page_obj = article_paginator.get_page(article_page)

    return {
        "popular_channel": [],
        "shorts": {
            "current_page": short_page_obj.number,
            "total_page": short_paginator.num_pages,
            "total_items": short_paginator.count,
            "items": ShortIslamiSerializer(
                short_page_obj,
                many=True,
                context={"request": request},
            ).data,
        },
        "artikel_islami": {
            "current_page": article_page_obj.number,
            "total_page": article_paginator.num_pages,
            "total_items": article_paginator.count,
            "items": ArtikelIslamiSerializer(
                article_page_obj,
                many=True,
                context={"request": request},
            ).data,
        },
    }


def increment_short_view(short_id):
    """
    Atomic increment view count
    """

    from django.db.models import F

    updated = (
        ShortIslami.objects
        .filter(
            id=short_id,
            is_published=True,
        )
        .update(
            view_count=F("view_count") + 1
        )
    )

    return updated > 0