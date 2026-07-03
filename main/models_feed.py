from django.db import models
from django.conf import settings

class Feed(models.Model):
    """Model for feed posts"""

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feeds')
    feed_caption = models.TextField(blank=True, null=True)
    feed_location = models.CharField(max_length=255, blank=True, null=True)
    feed_pictures = models.JSONField(default=list)  # List of image URLs
    user_country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    isSponsored = models.BooleanField(default=False)
    permalink = models.CharField(max_length=500, blank=True, null=True)
    tagged_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='tagged_in_feeds',
        blank=True
    )
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='public'
    )
    class Meta:
        db_table = 'social_feed'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['user_country']),
            models.Index(fields=['isSponsored']),
        ]
    
    def __str__(self):
        return f"Feed by {self.user.username} at {self.created_at}"


class FeedLike(models.Model):
    """Like pada feed"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_feed_like'
        unique_together = ('user', 'feed')
    
    def __str__(self):
        return f"{self.user.username} likes feed {self.feed.id}"


class FeedComment(models.Model):
    """Comment pada feed"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    replied_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replied_comments'
    )
    
    class Meta:
        db_table = 'social_feed_comment'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on feed {self.feed.id}"


class Follow(models.Model):
    """User following relationship"""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_follow'
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Story(models.Model):
    """Model untuk stories"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    story_link = models.URLField(max_length=500)
    user_country = models.CharField(max_length=100, blank=True, null=True)
    isOnline = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'social_story'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user_country']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Story by {self.user.username} at {self.created_at}"


class StorySeen(models.Model):
    """Track siapa saja yang sudah melihat story"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='seen_by')
    seen_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_story_seen'
        unique_together = ('user', 'story')
    
    def __str__(self):
        return f"{self.user.username} seen story {self.story.id}"

    

class CommentLike(models.Model):
    """Like pada komentar"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(FeedComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_comment_like'
        unique_together = ('user', 'comment')
    
    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"