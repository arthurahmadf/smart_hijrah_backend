# main/serializers/user_serializers.py
from rest_framework import serializers
from main.models import User
from main.my_utils import generate_url


class UserBasicSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nama', 'profile_picture', 'banner']
    
    def get_profile_picture(self, obj):
        return generate_url(obj.foto_profil, self.context.get('request'))
    
    def get_banner(self, obj):
        return generate_url(obj.banner, self.context.get('request'))