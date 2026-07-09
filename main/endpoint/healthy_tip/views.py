from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from main.models_healthy_tip import HealthyTip
from main.serializers.healthy_tip_serializers import HealthyTipSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_tips_hidup_sehat(request):
    try:
        base_queryset = (
            HealthyTip.objects
            .filter(is_published=True)
            .select_related("uploader")
            .order_by("-created_at")
        )

        tips_baru = base_queryset.filter(
            section=HealthyTip.Section.TIPS_BARU
        )

        seminar_sehat = base_queryset.filter(
            section=HealthyTip.Section.SEMINAR_SEHAT
        )

        all_tips = base_queryset

        context = {"request": request}

        return JsonResponse({
            "tips_baru": HealthyTipSerializer(tips_baru, many=True, context=context).data,
            "seminar_sehat": HealthyTipSerializer(seminar_sehat, many=True, context=context).data,
            "all_tips": HealthyTipSerializer(all_tips, many=True, context=context).data,
        }, status=200, safe=False)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e),
        }, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_tips_hidup_sehat(request, query):
    try:
        queryset = (
            HealthyTip.objects
            .filter(is_published=True)
            .filter(
                Q(title__icontains=query) |
                Q(description_short__icontains=query) |
                Q(category__icontains=query) |
                Q(article__icontains=query)
            )
            .select_related("uploader")
            .order_by("-created_at")
        )

        serializer = HealthyTipSerializer(
            queryset,
            many=True,
            context={"request": request},
        )

        return JsonResponse(serializer.data, status=200, safe=False)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e),
        }, status=400)