from rest_framework import serializers
from main.models_masjid import MasjidReview, MasjidReviewPhoto
from main.my_utils import generate_url

class MasjidReviewPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MasjidReviewPhoto
        fields = ['id', 'image_url', 'created_at']
    
    def get_image_url(self, obj):
        return generate_url(obj.image, self.context.get('request'))

class MasjidReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_picture = serializers.SerializerMethodField()
    photos = MasjidReviewPhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = MasjidReview
        fields = ['id', 'user', 'user_name', 'user_picture', 'rating', 'review', 
                  'photos', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_user_picture(self, obj):
        return generate_url(obj.user.foto_profil, self.context.get('request'))

class MasjidReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasjidReview
        fields = ['place_id', 'rating', 'review']