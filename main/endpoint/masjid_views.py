from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from main.models_masjid import MasjidReview, MasjidReviewPhoto
from main.serializers.masjid_serializers import MasjidReviewSerializer, MasjidReviewCreateSerializer
import requests
import uuid
from math import radians, sin, cos, sqrt, atan2

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
def nearby_masjids(request):
    """
    Get masjids near user's location with ratings from Smart Hijrah
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
        
        categories = "religion.place_of_worship.islam"
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
        from main.models_masjid import MasjidReview
        from django.db.models import Avg, Count
        
        reviews_aggregate = MasjidReview.objects.filter(
            place_id__in=place_ids
        ).values('place_id').annotate(
            avg_rating=Avg('rating'),
            review_count=Count('id')
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
                "name": props.get('name', 'Masjid'),
                "address": props.get('formatted', props.get('address_line2', '')),
                "review_score": final_rating,
                "review_count": final_review_count,
                "distance_km": round(distance_km, 2) if distance_km else None,
                "latitude": place_lat,
                "longitude": place_lon,
                "picture": None,
                "favorited": False
            })
        
        results.sort(key=lambda x: x['distance_km'] if x['distance_km'] else 999)
        
        return JsonResponse({
            "success": True,
            "data": results,
            "total": len(results),
            "user_location": {"lat": float(lat), "lng": float(lng)}
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def masjid_detail(request, place_id):
    """
    Get detailed information about a specific masjid using Place Details API
    """
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
        
        # Extract details
        details = data.get('features', [{}])[0].get('properties', {})
        
        return JsonResponse({
            "success": True,
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
def create_masjid_review(request, place_id):
    """
    Create or update review for a masjid
    Can upload multiple photos (max 5)
    """
    try:
        # Cek apakah user sudah pernah review masjid ini
        existing_review = MasjidReview.objects.filter(
            user=request.user,
            place_id=place_id
        ).first()
        
        # Ambil data dari request
        rating = request.POST.get('rating')
        review = request.POST.get('review', '')
        
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
        
        # Handle photos (max 5)
        photos = request.FILES.getlist('photos')
        if len(photos) > 5:
            return JsonResponse({
                "success": False,
                "message": "Maximum 5 photos per review"
            }, status=400)
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.review = review
            existing_review.save()
            masjid_review = existing_review
            
            # Hapus foto lama (opsional, atau biarkan)
            # MasjidReviewPhoto.objects.filter(review=masjid_review).delete()
        else:
            # Create new review
            serializer = MasjidReviewCreateSerializer(data={
                'place_id': place_id,
                'rating': rating,
                'review': review
            })
            
            if not serializer.is_valid():
                return JsonResponse({
                    "success": False,
                    "message": serializer.errors
                }, status=400)
            
            masjid_review = MasjidReview.objects.create(
                user=request.user,
                place_id=place_id,
                rating=rating,
                review=review
            )
        
        # Upload photos
        for photo in photos:
            if not photo.content_type.startswith('image'):
                continue
            
            file_extension = photo.name.split('.')[-1]
            new_filename = f"masjid_reviews/{request.user.id}/{place_id}/{uuid.uuid4()}.{file_extension}"
            saved_path = default_storage.save(new_filename, ContentFile(photo.read()))
            photo_url = request.build_absolute_uri(default_storage.url(saved_path))
            
            MasjidReviewPhoto.objects.create(
                review=masjid_review,
                image=photo_url
            )
        
        result_serializer = MasjidReviewSerializer(masjid_review, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "message": "Review saved successfully",
            "data": result_serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_masjid_reviews(request, place_id):
    """
    Get all reviews for a specific masjid
    """
    try:
        reviews = MasjidReview.objects.filter(place_id=place_id).select_related('user').prefetch_related('photos')
        
        # Hitung rating rata-rata
        avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
        review_count = reviews.count()
        
        serializer = MasjidReviewSerializer(reviews, many=True, context={'request': request})
        
        return JsonResponse({
            "success": True,
            "place_id": place_id,
            "average_rating": round(avg_rating, 1) if avg_rating else 0,
            "review_count": review_count,
            "reviews": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_masjid_review(request, review_id):
    """
    Delete user's own review
    """
    try:
        review = get_object_or_404(MasjidReview, id=review_id)
        
        if review.user.id != request.user.id:
            return JsonResponse({
                "success": False,
                "message": "You can only delete your own reviews"
            }, status=403)
        
        # Hapus foto-foto dari storage
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
def check_user_review(request, place_id):
    """
    Check if current user has reviewed this masjid
    """
    try:
        review = MasjidReview.objects.filter(
            user=request.user,
            place_id=place_id
        ).first()
        
        if review:
            serializer = MasjidReviewSerializer(review, context={'request': request})
            return JsonResponse({
                "success": True,
                "has_reviewed": True,
                "review": serializer.data
            }, status=200)
        else:
            return JsonResponse({
                "success": True,
                "has_reviewed": False,
                "review": None
            }, status=200)
            
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)