from rest_framework import serializers
from main.models_feed import Feed, FeedComment, FeedLike, Follow, Story, StorySeen
from main.models import User
from main.my_utils import generate_url


class UserBasicSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nama', 'profile_picture']
    
    def get_profile_picture(self, obj):
        return generate_url(obj.foto_profil, self.context.get('request'))


class FeedSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.nama', read_only=True)
    user_country = serializers.CharField(source='user.country', read_only=True)
    user_picture = serializers.SerializerMethodField()
    isLiked = serializers.SerializerMethodField()
    isFollowed = serializers.SerializerMethodField()
    visibility = serializers.CharField()
    class Meta:
        model = Feed
        fields = [
            'id', 'user_id', 'user_name', 'user_country', 'user_picture',
            'feed_location', 'feed_caption', 'feed_pictures', 'created_at',
            'isLiked', 'isFollowed', 'like_count', 'comment_count',
            'isSponsored', 'permalink','visibility'
        ]
    
    def get_user_picture(self, obj):
        return generate_url(obj.user.foto_profil, self.context.get('request'))
    
    def get_isLiked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FeedLike.objects.filter(feed=obj, user=request.user).exists()
        return False
    
    def get_isFollowed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj.user).exists()
        return False


class FeedCommentSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    replied_to = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedComment
        fields = ['id', 'user', 'text', 'parent', 'replied_to', 'replies', 'created_at']
    
    def get_replies(self, obj):
        # Hanya ambil reply level 2 (parent = obj)
        replies = obj.replies.all().order_by('created_at')
        return FeedCommentSerializer(replies, many=True, context=self.context).data


class StorySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_picture = serializers.SerializerMethodField()
    isSeen = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'user_id', 'user_name', 'user_country', 'story_link',
            'user_picture', 'isOnline', 'created_at', 'isSeen'
        ]
    
    def get_user_picture(self, obj):
        return generate_url(obj.user.foto_profil, self.context.get('request'))
    
    def get_isSeen(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StorySeen.objects.filter(story=obj, user=request.user).exists()
        return False


class FeedCommentSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    replied_to = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    
    class Meta:
        model = FeedComment
        fields = [
            'id', 'user', 'text', 'parent', 'replied_to', 'replies',
            'is_liked', 'like_count', 'created_at'
        ]
    
    def get_replies(self, obj):
        replies = obj.replies.all().order_by('created_at')
        return FeedCommentSerializer(replies, many=True, context=self.context).data
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from main.models_feed import CommentLike
            return CommentLike.objects.filter(comment=obj, user=request.user).exists()
        return False