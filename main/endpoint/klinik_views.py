from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models as db_models
from django.conf import settings
from main.models_klinik import KlinikReview, KlinikReviewPhoto
from main.serializers.klinik_serializers import KlinikReviewSerializer, KlinikReviewCreateSerializer
import requests
import uuid
from math import radians, sin, cos, sqrt, atan2
import traceback
import logging

# Setup logging
logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Hitung jarak antara dua koordinat dalam km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_kliniks(request):
    """
    Get clinics near user's location using Geoapify Places API
    Query params: lat, lng, radius (default 5000 meters), page, page_size
    """
    try:
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        radius = request.GET.get('radius', 5000)
        
        if not lat or not lng:
            return JsonResponse({
                "success": False,
                "message": "lat and lng parameters are required"
            }, status=400)
        
        # Kategori untuk klinik di Geoapify
        categories = "healthcare.clinic_or_praxis"
        
        url = "https://api.geoapify.com/v2/places"
        
        params = {
            "categories": categories,
            "filter": f"circle:{lng},{lat},{radius}",
            "limit": 50,
            "apiKey": settings.GEOAPIFY_API_KEY
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return JsonResponse({
                "success": False,
                "message": f"Geoapify API error: {response.text}"
            }, status=500)
        
        data = response.json()
        features = data.get('features', [])
        
        # Kumpulkan semua place_id untuk query rating ke database
        place_ids = []
        for feature in features:
            props = feature.get('properties', {})
            place_id = props.get('place_id')
            if place_id:
                place_ids.append(place_id)
        
        # Ambil semua rating dari database untuk place_ids ini
        reviews_aggregate = KlinikReview.objects.filter(
            place_id__in=place_ids
        ).values('place_id').annotate(
            avg_rating=db_models.Avg('rating'),
            review_count=db_models.Count('id')
        )
        
        # Buat dictionary untuk quick lookup
        rating_map = {}
        for agg in reviews_aggregate:
            rating_map[agg['place_id']] = {
                'rating': round(agg['avg_rating'], 1) if agg['avg_rating'] else 0,
                'review_count': agg['review_count']
            }
        
        # Format response
        results = []
        for feature in features:
            props = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            place_lon = coordinates[0] if len(coordinates) > 0 else None
            place_lat = coordinates[1] if len(coordinates) > 1 else None
            place_id = props.get('place_id')
            
            distance_km = calculate_distance(
                float(lat), float(lng),
                place_lat, place_lon
            ) if place_lat and place_lon else None
            
            # Ambil rating dari database (jika ada), fallback ke rating Geoapify
            db_rating = rating_map.get(place_id, {})
            final_rating = db_rating.get('rating', props.get('rating', 0))
            final_review_count = db_rating.get('review_count', 0)
            
            results.append({
                "id": place_id,
                "name": props.get('name', 'Klinik'),
                "address": props.get('formatted', props.get('address_line2', '')),
                "review_score": final_rating,
                "review_count": final_review_count,
                "distance_km": round(distance_km, 2) if distance_km else None,
                "latitude": place_lat,
                "longitude": place_lon,
                "picture": None,
                "favorited": False
            })
        
        # Urutkan berdasarkan jarak
        results.sort(key=lambda x: x['distance_km'] if x['distance_km'] else 999)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        total_items = len(results)
        total_page = (total_items + page_size - 1) // page_size if page_size > 0 else 1
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = results[start:end]
        
        paginated_data = {
            'current_page': page,
            'total_page': total_page,
            'total_items': total_items,
            'kliniks': paginated_results
        }
        
        return JsonResponse({
            "success": True,
            "message": "Kliniks fetched successfully",
            "data": paginated_data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def klinik_detail(request, place_id):
    """Get detailed information about a specific clinic"""
    try:
        url = f"https://api.geoapify.com/v2/place-details"
        
        params = {
            "id": place_id,
            "features": "details",
            "apiKey": settings.GEOAPIFY_API_KEY
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return JsonResponse({
                "success": False,
                "message": f"Geoapify API error: {response.text}"
            }, status=500)
        
        data = response.json()
        details = data.get('features', [{}])[0].get('properties', {})
        
        return JsonResponse({
            "success": True,
            "message": "Klinik detail fetched successfully",
            "data": {
                "id": place_id,
                "name": details.get('name'),
                "address": details.get('formatted'),
                "latitude": details.get('lat'),
                "longitude": details.get('lon'),
                "website": details.get('website'),
                "phone": details.get('phone'),
                "opening_hours": details.get('opening_hours'),
                "rating": details.get('rating', 0)
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_klinik_review(request, place_id):
    """Create or update review for a clinic with photos (max 5)"""
    try:
        print(f"=== DEBUG: Starting create_klinik_review ===")
        print(f"place_id: {place_id}")
        print(f"place_id length: {len(place_id)}")
        
        existing_review = KlinikReview.objects.filter(
            user=request.user,
            place_id=place_id
        ).first()
        
        rating = request.POST.get('rating')
        review = request.POST.get('review', '')
        
        print(f"rating: {rating}")
        print(f"review: {review[:50] if review else 'None'}")
        
        if not rating:
            return JsonResponse({
                "success": False,
                "message": "Rating is required"
            }, status=400)
        
        rating = int(rating)
        if rating < 1 or rating > 5:
            return JsonResponse({
                "success": False,
                "message": "Rating must be between 1 and 5"
            }, status=400)
        
        photos = request.FILES.getlist('photos')
        print(f"number of photos: {len(photos)}")
        
        if len(photos) > 5:
            return JsonResponse({
                "success": False,
                "message": "Maximum 5 photos per review"
            }, status=400)
        
        print("=== Saving to database ===")
        
        if existing_review:
            print("Updating existing review")
            existing_review.rating = rating
            existing_review.review = review
            existing_review.save()
            klinik_review = existing_review
        else:
            print("Creating new review")
            klinik_review = KlinikReview.objects.create(
                user=request.user,
                place_id=place_id,
                rating=rating,
                review=review
            )
            print(f"Created review with id: {klinik_review.id}")
        
        # Upload photos
        for photo in photos:
            if not photo.content_type.startswith('image'):
                continue
            
            # Langsung assign file object ke ImageField
            KlinikReviewPhoto.objects.create(
                review=klinik_review,
                image=photo
            )
        
        serializer = KlinikReviewSerializer(klinik_review, context={'request': request})
        
        print("=== Success ===")
        return JsonResponse({
            "success": True,
            "message": "Review saved successfully",
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        print("=== ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Full stack trace:")
        traceback.print_exc()
        
        return JsonResponse({
            "success": False, 
            "message": str(e),
            "error_type": type(e).__name__,
            "stack_trace": traceback.format_exc()
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_klinik_reviews(request, place_id):
    """Get all reviews for a specific clinic with pagination"""
    try:
        reviews = KlinikReview.objects.filter(place_id=place_id).select_related('user').prefetch_related('photos')
        
        avg_rating = reviews.aggregate(db_models.Avg('rating'))['rating__avg']
        review_count = reviews.count()
        
        # Pagination untuk reviews
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        total_items = review_count
        total_page = (total_items + page_size - 1) // page_size if page_size > 0 else 1
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_reviews = reviews[start:end]
        
        serializer = KlinikReviewSerializer(paginated_reviews, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Reviews fetched successfully",
            "data": {
                "place_id": place_id,
                "average_rating": round(avg_rating, 1) if avg_rating else 0,
                "total_review_count": review_count,
                "current_page": page,
                "total_page": total_page,
                "reviews": serializer.data
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_klinik_review(request, review_id):
    """Delete user's own review"""
    try:
        review = get_object_or_404(KlinikReview, id=review_id)
        
        if review.user.id != request.user.id:
            return JsonResponse({
                "success": False,
                "message": "You can only delete your own reviews"
            }, status=403)
        
        for photo in review.photos.all():
            default_storage.delete(photo.image.name)
        
        review.delete()
        
        return JsonResponse({
            "success": True,
            "message": "Review deleted successfully"
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_klinik_review(request, place_id):
    """Check if current user has reviewed this clinic"""
    try:
        review = KlinikReview.objects.filter(
            user=request.user,
            place_id=place_id
        ).first()
        
        if review:
            serializer = KlinikReviewSerializer(review, context={'request': request})
            return JsonResponse({
                "success": True,
                "has_reviewed": True,
                "data": serializer.data
            }, status=200)
        else:
            return JsonResponse({
                "success": True,
                "has_reviewed": False,
                "data": None
            }, status=200)
            
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)