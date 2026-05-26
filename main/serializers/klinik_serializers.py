from rest_framework import serializers
from main.models_klinik import KlinikReview, KlinikReviewPhoto
from main.my_utils import generate_url

class KlinikReviewPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = KlinikReviewPhoto
        fields = ['id', 'image_url', 'created_at']
    
    def get_image_url(self, obj):
        return generate_url(obj.image, self.context.get('request'))

class KlinikReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_picture = serializers.SerializerMethodField()
    photos = KlinikReviewPhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = KlinikReview
        fields = ['id', 'user', 'user_name', 'user_picture', 'rating', 'review', 
                  'photos', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_user_picture(self, obj):
        return generate_url(obj.user.foto_profil, self.context.get('request'))

class KlinikReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KlinikReview
        fields = ['place_id', 'rating', 'review']