from rest_framework import serializers
from main.models_feed import Feed, FeedPicture, FeedLike, FeedComment, Follow, Story, StorySeen
from main.models import User

class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer untuk user (basic info)"""
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nama', 'profile_picture']
    
    def get_profile_picture(self, obj):
        from main.my_utils import generate_url
        return generate_url(obj.foto_profil, self.context.get('request'))

class FeedPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedPicture
        fields = ['id', 'image', 'order']

class FeedSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    pictures = FeedPictureSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    
    class Meta:
        model = Feed
        fields = [
            'id', 'user', 'caption', 'location', 'pictures',
            'created_at', 'like_count', 'comment_count',
            'is_sponsored', 'permalink', 'is_liked', 'is_followed'
        ]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FeedLike.objects.filter(feed=obj, user=request.user).exists()
        return False
    
    def get_is_followed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj.user).exists()
        return False

class StorySerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    is_seen = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = ['id', 'user', 'media_url', 'media_type', 'created_at', 'is_seen']
    
    def get_is_seen(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StorySeen.objects.filter(story=obj, user=request.user).exists()
        return False


class FeedCommentSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = FeedComment
        fields = ['id', 'user', 'text', 'created_at']

class FeedDetailSerializer(FeedSerializer):
    comments = FeedCommentSerializer(many=True, read_only=True)
    
    class Meta(FeedSerializer.Meta):
        fields = FeedSerializer.Meta.fields + ['comments']